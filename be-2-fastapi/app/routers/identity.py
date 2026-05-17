from fastapi import APIRouter, Depends

from app.auth.azure import AzureTokenClaims
from app.auth.dependencies import get_current_claims, get_current_identity
from app.db.models import ApiIdentity

router = APIRouter(tags=["identity"])


@router.get("/me")
def me(
    identity: ApiIdentity = Depends(get_current_identity),
    claims: AzureTokenClaims = Depends(get_current_claims),
):
    groups = claims.raw.get("groups")
    if isinstance(groups, list) and len(groups) > 20:
        groups = {"truncated": True, "sample": groups[:20]}

    return {
        "authenticated": True,
        "local": {
            "id": identity.id,
            "azure_oid": identity.azure_oid,
            "email": identity.email,
            "display_name": identity.display_name,
        },
        "token_claims": {
            "oid": claims.azure_oid,
            "tid": claims.tenant_id,
            "email": claims.email,
            "preferred_username": claims.preferred_username,
            "name": claims.name,
            "groups": groups,
        },
    }


@router.get("/protected")
def protected(identity: ApiIdentity = Depends(get_current_identity)):
    return {
        "message": "This route requires a valid Azure Bearer access token.",
        "azure_oid": identity.azure_oid,
    }
