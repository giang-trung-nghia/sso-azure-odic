"""
Validate Microsoft Entra ID access tokens (Bearer JWT) using JWKS.

Checks: signature (RS256), issuer, audience, expiration, tenant (`tid`).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import jwt
from jwt import PyJWKClient

from app.config import Settings

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class AzureTokenClaims:
    """Normalized identity extracted from a validated access token."""

    azure_oid: str
    tenant_id: str
    email: str | None
    preferred_username: str | None
    name: str | None
    raw: dict[str, Any]


class AzureJWTValidator:
    def __init__(self, settings: Settings) -> None:
        if not settings.azure_auth_enabled:
            raise RuntimeError("Azure JWT validator requires tenant id and client id.")
        self._settings = settings
        self._jwks = PyJWKClient(settings.azure_jwks_url, cache_keys=True)

    def validate(self, token: str) -> AzureTokenClaims:
        signing_key = self._jwks.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=self._settings.azure_audience,
            issuer=self._settings.azure_issuer,
            options={
                "require": ["exp", "iss", "aud"],
            },
        )

        tid = payload.get("tid")
        if tid != self._settings.azure_ad_tenant_id:
            raise jwt.InvalidTokenError(
                f"Unexpected tenant id: {tid!r} (expected {self._settings.azure_ad_tenant_id!r})"
            )

        azure_oid = payload.get("oid") or payload.get("sub")
        if not azure_oid:
            raise jwt.InvalidTokenError("Token missing oid/sub claim.")

        return AzureTokenClaims(
            azure_oid=str(azure_oid),
            tenant_id=str(tid),
            email=payload.get("email") or payload.get("upn"),
            preferred_username=payload.get("preferred_username"),
            name=payload.get("name"),
            raw=dict(payload),
        )


_validator: AzureJWTValidator | None = None


def get_validator(settings: Settings) -> AzureJWTValidator:
    global _validator
    if _validator is None:
        _validator = AzureJWTValidator(settings)
    return _validator
