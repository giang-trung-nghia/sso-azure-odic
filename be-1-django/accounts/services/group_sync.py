"""
Persist group memberships from OIDC claims and resolve names via Microsoft Graph.
"""

from __future__ import annotations

import logging
from typing import Any

from django.utils import timezone

from accounts.models import AzureGroup, AzureUserProfile
from accounts.services.graph_groups import GraphGroupClient
from accounts.services.group_claims import extract_group_object_ids

LOGGER = logging.getLogger(__name__)


def sync_user_groups(
    profile: AzureUserProfile,
    claims: dict[str, Any],
    access_token: str | None,
) -> None:
    object_ids = extract_group_object_ids(claims, access_token)
    graph_groups: list[dict[str, Any]] = []

    if access_token:
        client = GraphGroupClient(access_token)
        if object_ids:
            try:
                graph_groups = client.resolve_groups(object_ids)
            except Exception as exc:
                LOGGER.warning("Graph resolve_groups failed: %s", exc)
        else:
            try:
                graph_groups = client.list_member_of_groups()
                object_ids = [g["id"] for g in graph_groups if g.get("id")]
            except Exception as exc:
                LOGGER.warning("Graph memberOf fallback failed: %s", exc)

    azure_groups = _upsert_groups_from_ids(object_ids)
    profile.groups.set(azure_groups)

    if graph_groups:
        _apply_graph_metadata(graph_groups)

    profile.last_synced_at = timezone.now()
    profile.save(update_fields=["last_synced_at"])


def _upsert_groups_from_ids(object_ids: list[str]) -> list[AzureGroup]:
    groups: list[AzureGroup] = []
    for oid in object_ids:
        group, _created = AzureGroup.objects.get_or_create(object_id=oid)
        groups.append(group)
    return groups


def _apply_graph_metadata(graph_items: list[dict[str, Any]]) -> None:
    now = timezone.now()
    for item in graph_items:
        oid = item.get("id")
        if not oid:
            continue
        AzureGroup.objects.filter(object_id=oid).update(
            display_name=item.get("displayName") or "",
            description=item.get("description") or "",
            mail=item.get("mail") or "",
            mail_enabled=item.get("mailEnabled"),
            security_enabled=item.get("securityEnabled"),
            graph_raw=item,
            resolved_at=now,
        )
