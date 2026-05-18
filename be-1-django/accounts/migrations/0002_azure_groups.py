import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def copy_user_profiles(apps, schema_editor):
    UserProfile = apps.get_model("accounts", "UserProfile")
    AzureUserProfile = apps.get_model("accounts", "AzureUserProfile")
    for old in UserProfile.objects.all():
        AzureUserProfile.objects.get_or_create(
            user_id=old.user_id,
            defaults={"azure_oid": old.azure_oid},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AzureGroup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("object_id", models.CharField(db_index=True, max_length=64, unique=True)),
                ("display_name", models.CharField(blank=True, max_length=255)),
                ("description", models.TextField(blank=True)),
                ("mail", models.EmailField(blank=True, max_length=254)),
                ("security_enabled", models.BooleanField(blank=True, null=True)),
                ("mail_enabled", models.BooleanField(blank=True, null=True)),
                ("graph_raw", models.JSONField(blank=True, default=dict)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Azure group",
                "verbose_name_plural": "Azure groups",
                "ordering": ["display_name", "object_id"],
            },
        ),
        migrations.CreateModel(
            name="AzureUserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("azure_oid", models.CharField(db_index=True, max_length=64, unique=True)),
                ("tenant_id", models.CharField(blank=True, db_index=True, max_length=64)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("display_name", models.CharField(blank=True, max_length=255)),
                ("last_synced_at", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="azure_profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("groups", models.ManyToManyField(blank=True, related_name="members", to="accounts.azuregroup")),
            ],
            options={
                "verbose_name": "Azure user profile",
                "verbose_name_plural": "Azure user profiles",
            },
        ),
        migrations.RunPython(copy_user_profiles, migrations.RunPython.noop),
        migrations.DeleteModel(
            name="UserProfile",
        ),
    ]
