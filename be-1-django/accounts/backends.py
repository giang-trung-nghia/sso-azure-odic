from __future__ import annotations

import logging

from django.contrib.auth import get_user_model
from django.core.exceptions import SuspiciousOperation
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from accounts.models import AzureUserProfile
from accounts.services.group_sync import sync_user_groups

LOGGER = logging.getLogger(__name__)


class EntraOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    """
    Entra ID (Azure AD) OIDC backend.

    - Matches users by `AzureUserProfile.azure_oid`.
    - Merges ID token claims with Microsoft Graph `/oidc/userinfo`.
    - Syncs group object IDs + Graph-resolved display names to PostgreSQL.
    """

    def verify_claims(self, claims) -> bool:
        if not (claims.get("oid") or claims.get("sub")):
            return False
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
            profile = AzureUserProfile.objects.select_related("user").get(azure_oid=oid)
            return self.UserModel.objects.filter(pk=profile.user_id)
        except AzureUserProfile.DoesNotExist:
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

        profile = AzureUserProfile.objects.create(
            user=user,
            azure_oid=oid,
            tenant_id=str(claims.get("tid") or ""),
            email=str(email),
            display_name=str(claims.get("name") or ""),
        )
        LOGGER.info("Provisioned Django user for Entra oid=%s", oid)
        return user

    def update_user(self, user, claims):
        email = claims.get("email") or claims.get("preferred_username")
        if email:
            user.email = str(email)[:254]
        user.set_unusable_password()
        user.save()

        oid = claims.get("oid") or claims.get("sub")
        profile, _created = AzureUserProfile.objects.get_or_create(
            user=user,
            defaults={
                "azure_oid": oid or "",
                "tenant_id": str(claims.get("tid") or ""),
                "email": str(email or user.email or "")[:254],
                "display_name": str(claims.get("name") or ""),
            },
        )
        if oid and profile.azure_oid != oid:
            profile.azure_oid = oid
        profile.tenant_id = str(claims.get("tid") or profile.tenant_id)
        if email:
            profile.email = str(email)[:254]
        name = claims.get("name")
        if name:
            profile.display_name = str(name)[:255]
        profile.save()
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
            user = self.update_user(users[0], merged)
        elif len(users) > 1:
            raise SuspiciousOperation("Multiple users matched Entra claims.")
        elif self.get_settings("OIDC_CREATE_USER", True):
            user = self.create_user(merged)
        else:
            LOGGER.warning(
                "Login failed: no AzureUserProfile for oid=%s and OIDC_CREATE_USER is False",
                oid,
            )
            return None

        profile = AzureUserProfile.objects.get(user=user)
        try:
            sync_user_groups(profile, merged, access_token)
        except Exception as exc:
            LOGGER.exception("Group sync failed for oid=%s: %s", oid, exc)

        self._stash_claims_snapshot(merged)
        return user

    def _stash_claims_snapshot(self, claims) -> None:
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
            "has_group_overage": "groups" in (claims.get("_claim_names") or {}),
        }
        request.session.modified = True
