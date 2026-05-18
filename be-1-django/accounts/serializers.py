"""JSON shapes for API responses (no DRF)."""

from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser
from django.http import HttpRequest

from accounts.models import AzureUserProfile


def build_api_me_payload(user: AbstractBaseUser, request: HttpRequest) -> dict:
    profile = (
        AzureUserProfile.objects.filter(user=user)
        .prefetch_related("groups")
        .first()
    )

    expiry = request.session.get_expiry_date()
    auth_block = {
        "mode": "django_session",
        "session_key_prefix": request.session.session_key[:8] + "…"
        if request.session.session_key
        else None,
        "session_expires_at": expiry.isoformat() if expiry else None,
        "session_expires_in_seconds": request.session.get_expiry_age(),
    }

    if not profile:
        return {
            "authenticated": True,
            "username": user.username,
            "email": user.email,
            "azure_oid": None,
            "tenant_id": None,
            "display_name": None,
            "groups": [],
            "group_object_ids": [],
            "group_display_names": [],
            "auth": auth_block,
        }

    groups_payload = [
        {
            "object_id": g.object_id,
            "display_name": g.display_name or "",
            "description": g.description or "",
            "mail": g.mail or "",
            "security_enabled": g.security_enabled,
            "mail_enabled": g.mail_enabled,
            "resolved_at": g.resolved_at.isoformat() if g.resolved_at else None,
        }
        for g in profile.groups.all()
    ]

    return {
        "authenticated": True,
        "username": user.username,
        "email": profile.email or user.email,
        "azure_oid": profile.azure_oid,
        "tenant_id": profile.tenant_id,
        "display_name": profile.display_name,
        "last_synced_at": profile.last_synced_at.isoformat() if profile.last_synced_at else None,
        "groups": groups_payload,
        "group_object_ids": [g["object_id"] for g in groups_payload],
        "group_display_names": [g["display_name"] or "(unresolved)" for g in groups_payload],
        "auth": auth_block,
    }
