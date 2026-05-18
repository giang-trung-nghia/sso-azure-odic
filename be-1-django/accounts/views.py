from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse


def login_start(request):
    """Friendly entry point → mozilla-django-oidc authorize (authorization code flow)."""
    if not getattr(settings, "OIDC_ENABLED", False):
        return JsonResponse(
            {
                "detail": "OIDC is disabled. Set AZURE_AD_TENANT_ID, AZURE_AD_CLIENT_ID, "
                "and AZURE_AD_CLIENT_SECRET in the environment.",
            },
            status=503,
        )
    next_url = request.GET.get("next")
    target = reverse("oidc_authentication_init")
    if next_url:
        return redirect(f"{target}?next={next_url}")
    return redirect(target)


def me(request):
    """Session auth status for SPA clients (401 JSON instead of redirect)."""
    if not request.user.is_authenticated:
        return JsonResponse({"authenticated": False}, status=401)

    profile = getattr(request.user, "profile", None)
    expiry = request.session.get_expiry_date()
    return JsonResponse(
        {
            "authenticated": True,
            "username": request.user.username,
            "email": request.user.email,
            "azure_oid": getattr(profile, "azure_oid", None),
            "is_staff": request.user.is_staff,
            "auth": {
                "mode": "django_session",
                "session_key_prefix": request.session.session_key[:8] + "…"
                if request.session.session_key
                else None,
                "session_expires_at": expiry.isoformat() if expiry else None,
                "session_expires_in_seconds": request.session.get_expiry_age(),
            },
        }
    )


@login_required
def claims_inspect(request):
    """
    Inspect selected Entra claims last seen at login (session snapshot).

    Full group lists may be omitted by Entra (overage) unless optional claims are configured.
    """
    profile = getattr(request.user, "profile", None)
    return JsonResponse(
        {
            "user": {
                "username": request.user.username,
                "email": request.user.email,
                "azure_oid": getattr(profile, "azure_oid", None),
            },
            "session_claims_snapshot": request.session.get("oidc_claims_snapshot"),
            "session_has_access_token": bool(request.session.get("oidc_access_token")),
            "session_has_id_token": bool(request.session.get("oidc_id_token")),
        }
    )
