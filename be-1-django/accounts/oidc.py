"""Build Microsoft Entra (v2) end-session URL after Django logout."""

from urllib.parse import quote

from django.conf import settings


def provider_logout_url(request):
    """
    Called by mozilla-django-oidc *before* Django clears the session.

    Returns the URL the browser should visit next (Entra logout),
    with a safe post-logout redirect back to our SPA or home page.
    """
    tenant = getattr(settings, "AZURE_AD_TENANT_ID", "") or ""
    if not tenant:
        return ""

    target = getattr(settings, "ENTRA_POST_LOGOUT_REDIRECT_URI", "") or ""
    if not target:
        target = request.build_absolute_uri(settings.LOGOUT_REDIRECT_URL)

    encoded = quote(target, safe="")
    return (
        f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/logout"
        f"?post_logout_redirect_uri={encoded}"
    )
