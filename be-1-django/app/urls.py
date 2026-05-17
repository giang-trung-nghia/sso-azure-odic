"""
URL configuration for app project.
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from .health import health

urlpatterns = [
    path("health/", health, name="health"),
]

if getattr(settings, "OIDC_ENABLED", False):
    urlpatterns += [
        path("oidc/", include("mozilla_django_oidc.urls")),
    ]

urlpatterns += [
    path("accounts/", include("accounts.urls")),
    path("admin/", admin.site.urls),
]
