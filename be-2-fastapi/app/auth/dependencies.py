"""
FastAPI dependencies for Bearer JWT authentication.
"""

from __future__ import annotations

import logging

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.azure import AzureTokenClaims, get_validator
from app.config import Settings, get_settings
from app.db.models import ApiIdentity
from app.db.session import get_db

LOGGER = logging.getLogger(__name__)
_bearer = HTTPBearer(auto_error=False)


def require_azure_auth(settings: Settings = Depends(get_settings)) -> None:
    if not settings.azure_auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Azure JWT auth is disabled. Set AZURE_AD_TENANT_ID and "
                "AZURE_AD_CLIENT_ID (and optional AZURE_AD_API_AUDIENCE)."
            ),
        )


def get_current_claims(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_azure_auth),
) -> AzureTokenClaims:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        return get_validator(settings).validate(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except jwt.InvalidTokenError as exc:
        LOGGER.info("JWT validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or untrusted access token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_identity(
    claims: AzureTokenClaims = Depends(get_current_claims),
    db=Depends(get_db),
) -> ApiIdentity:
    """Validate JWT and return (or create) local row keyed by `azure_oid`."""
    identity = db.query(ApiIdentity).filter(ApiIdentity.azure_oid == claims.azure_oid).one_or_none()
    if identity is None:
        identity = ApiIdentity(
            azure_oid=claims.azure_oid,
            email=claims.email or claims.preferred_username,
            display_name=claims.name,
        )
        db.add(identity)
        db.commit()
        db.refresh(identity)
    else:
        changed = False
        email = claims.email or claims.preferred_username
        if email and identity.email != email:
            identity.email = email
            changed = True
        if claims.name and identity.display_name != claims.name:
            identity.display_name = claims.name
            changed = True
        if changed:
            db.commit()
            db.refresh(identity)
    return identity
