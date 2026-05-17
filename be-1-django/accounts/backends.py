from __future__ import annotations

import logging

from django.contrib.auth import get_user_model
from django.core.exceptions import SuspiciousOperation
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from accounts.models import UserProfile

LOGGER = logging.getLogger(__name__)


class EntraOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    """
    Entra ID (Azure AD) OIDC backend.

    - Matches users by `UserProfile.azure_oid` (stable Entra `oid` claim).
    - Merges ID token claims with Microsoft Graph `/oidc/userinfo` so `oid` / `tid`
      are available even when userinfo is sparse.
    - Forces unusable Django passwords (identity lives in Entra).
    """

    def verify_claims(self, claims) -> bool:
        if not (claims.get("oid") or claims.get("sub")):
            return False
        # Entra may omit `email` until optional claims / scopes are configured.
        return bool(
            claims.get("email")
            or claims.get("preferred_username")
            or claims.get("upn")
            or claims.get("oid")
        )

    def get_username(self, claims):
        oid = claims.get("oid") or claims.get("sub")
        if not oid:
            raise SuspiciousOperation("Entra login missing oid/sub claim")
        return f"entra_{oid}"[:150]

    def filter_users_by_claims(self, claims):
        oid = claims.get("oid") or claims.get("sub")
        if not oid:
            return self.UserModel.objects.none()
        try:
            profile = UserProfile.objects.select_related("user").get(azure_oid=oid)
            return self.UserModel.objects.filter(pk=profile.user_id)
        except UserProfile.DoesNotExist:
            return self.UserModel.objects.none()

    def create_user(self, claims):
        UserModel = get_user_model()
        username = self.get_username(claims)
        email = (claims.get("email") or claims.get("preferred_username") or "")[:254]
        oid = claims.get("oid") or claims.get("sub")
        if not oid:
            raise SuspiciousOperation("Cannot create user without oid")

        user = UserModel(username=username, email=email)
        user.set_unusable_password()
        user.save()

        UserProfile.objects.create(user=user, azure_oid=oid)
        self._stash_claims_snapshot(claims)
        LOGGER.info("Provisioned Django user for Entra oid=%s", oid)
        return user

    def update_user(self, user, claims):
        email = claims.get("email") or claims.get("preferred_username")
        if email:
            user.email = str(email)[:254]
        user.set_unusable_password()
        user.save()

        oid = claims.get("oid") or claims.get("sub")
        profile, _created = UserProfile.objects.get_or_create(
            user=user,
            defaults={"azure_oid": oid or ""},
        )
        if oid and profile.azure_oid != oid:
            profile.azure_oid = oid
            profile.save()

        self._stash_claims_snapshot(claims)
        return user

    def get_or_create_user(self, access_token, id_token, payload):
        user_info = self.get_userinfo(access_token, id_token, payload)
        merged = {**payload, **user_info}
        oid = merged.get("oid") or merged.get("sub")
        if oid:
            merged["oid"] = oid

        if not self.verify_claims(merged):
            raise SuspiciousOperation("Claims verification failed.")

        users = self.filter_users_by_claims(merged)
        if len(users) == 1:
            return self.update_user(users[0], merged)
        if len(users) > 1:
            raise SuspiciousOperation("Multiple users matched Entra claims.")

        if self.get_settings("OIDC_CREATE_USER", True):
            return self.create_user(merged)

        LOGGER.warning(
            "Login failed: no UserProfile for oid=%s and OIDC_CREATE_USER is False",
            oid,
        )
        return None

    def _stash_claims_snapshot(self, claims) -> None:
        """Store a small, inspectable snapshot (educational / debugging)."""
        request = getattr(self, "request", None)
        if not request or not hasattr(request, "session"):
            return

        groups = claims.get("groups")
        if isinstance(groups, list) and len(groups) > 50:
            groups = {"note": "truncated", "items": groups[:50]}

        request.session["oidc_claims_snapshot"] = {
            "oid": claims.get("oid"),
            "tid": claims.get("tid"),
            "email": claims.get("email"),
            "preferred_username": claims.get("preferred_username"),
            "groups": groups,
        }
        request.session.modified = True
