from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """Lightweight link between Django user and Entra object id (`oid`)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    azure_oid = models.CharField(max_length=64, unique=True, db_index=True)

    def __str__(self) -> str:
        return f"{self.user.username} → {self.azure_oid}"
