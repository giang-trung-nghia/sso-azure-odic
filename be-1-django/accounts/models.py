from django.conf import settings
from django.db import models


class AzureUserProfile(models.Model):
    """Entra identity linked to a Django user (stable `oid`)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="azure_profile",
    )
    azure_oid = models.CharField(max_length=64, unique=True, db_index=True)
    tenant_id = models.CharField(max_length=64, blank=True, db_index=True)
    email = models.EmailField(blank=True)
    display_name = models.CharField(max_length=255, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    groups = models.ManyToManyField(
        "AzureGroup",
        related_name="members",
        blank=True,
    )

    class Meta:
        verbose_name = "Azure user profile"
        verbose_name_plural = "Azure user profiles"

    def __str__(self) -> str:
        return f"{self.user.username} → {self.azure_oid}"


class AzureGroup(models.Model):
    """Azure AD group directory object (keyed by Entra object ID / GUID)."""

    object_id = models.CharField(max_length=64, unique=True, db_index=True)
    display_name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    mail = models.EmailField(blank=True)
    security_enabled = models.BooleanField(null=True, blank=True)
    mail_enabled = models.BooleanField(null=True, blank=True)
    graph_raw = models.JSONField(default=dict, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Azure group"
        verbose_name_plural = "Azure groups"
        ordering = ["display_name", "object_id"]

    def __str__(self) -> str:
        label = self.display_name or self.object_id
        return f"{label} ({self.object_id})"
