from django.contrib import admin

from accounts.models import AzureGroup, AzureUserProfile


@admin.register(AzureUserProfile)
class AzureUserProfileAdmin(admin.ModelAdmin):
    list_display = ("azure_oid", "email", "tenant_id", "user", "last_synced_at")
    search_fields = ("azure_oid", "email", "user__username")
    filter_horizontal = ("groups",)


@admin.register(AzureGroup)
class AzureGroupAdmin(admin.ModelAdmin):
    list_display = ("display_name", "object_id", "security_enabled", "resolved_at")
    search_fields = ("object_id", "display_name")
