from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_GET

from accounts.models import AzureUserProfile
from accounts.serializers import build_api_me_payload


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


@require_GET
def api_me(request):
    """Full identity + Azure groups for authenticated SPA clients."""
    if not request.user.is_authenticated:
        return JsonResponse({"authenticated": False}, status=401)
    return JsonResponse(build_api_me_payload(request.user, request))


@require_GET
def me(request):
    """Legacy endpoint — same payload as /api/me/."""
    if not request.user.is_authenticated:
        return JsonResponse({"authenticated": False}, status=401)
    return JsonResponse(build_api_me_payload(request.user, request))


@login_required
@require_GET
def claims_inspect(request):
    """Debug: session snapshot from last OIDC login."""
    profile = AzureUserProfile.objects.filter(user=request.user).first()
    return JsonResponse(
        {
            "user": {
                "username": request.user.username,
                "email": request.user.email,
                "azure_oid": profile.azure_oid if profile else None,
            },
            "session_claims_snapshot": request.session.get("oidc_claims_snapshot"),
            "session_has_access_token": bool(request.session.get("oidc_access_token")),
            "session_has_id_token": bool(request.session.get("oidc_id_token")),
        }
    )
