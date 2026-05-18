"""
Microsoft Graph API — resolve group object IDs to display names and metadata.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

LOGGER = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
GET_BY_IDS_CHUNK = 500


class GraphGroupClient:
    def __init__(self, access_token: str) -> None:
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

    def resolve_groups(self, object_ids: list[str]) -> list[dict[str, Any]]:
        if not object_ids:
            return []
        resolved: list[dict[str, Any]] = []
        for chunk in _chunks(object_ids, GET_BY_IDS_CHUNK):
            resolved.extend(self._get_by_ids(chunk))
        found_ids = {item["id"] for item in resolved}
        missing = [oid for oid in object_ids if oid not in found_ids]
        for oid in missing:
            item = self._get_group(oid)
            if item:
                resolved.append(item)
        return resolved

    def list_member_of_groups(self) -> list[dict[str, Any]]:
        """Fallback when `groups` claim is absent — delegated /me/memberOf."""
        url = f"{GRAPH_BASE}/me/memberOf/microsoft.graph.group"
        params = {
            "$select": "id,displayName,description,mail,mailEnabled,securityEnabled",
        }
        results: list[dict[str, Any]] = []
        while url:
            response = requests.get(url, headers=self._headers, params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
            for item in payload.get("value", []):
                if item.get("id"):
                    results.append(_normalize_group(item))
            url = payload.get("@odata.nextLink")
            params = None
        return results

    def _get_by_ids(self, object_ids: list[str]) -> list[dict[str, Any]]:
        response = requests.post(
            f"{GRAPH_BASE}/directoryObjects/getByIds",
            headers={**self._headers, "Content-Type": "application/json"},
            json={"ids": object_ids, "types": ["group"]},
            timeout=30,
        )
        response.raise_for_status()
        return [_normalize_group(item) for item in response.json().get("value", [])]

    def _get_group(self, object_id: str) -> dict[str, Any] | None:
        response = requests.get(
            f"{GRAPH_BASE}/groups/{object_id}",
            headers=self._headers,
            params={
                "$select": "id,displayName,description,mail,mailEnabled,securityEnabled",
            },
            timeout=30,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return _normalize_group(response.json())


def _normalize_group(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("id", ""),
        "displayName": item.get("displayName") or "",
        "description": item.get("description") or "",
        "mail": item.get("mail") or "",
        "mailEnabled": item.get("mailEnabled"),
        "securityEnabled": item.get("securityEnabled"),
        "@odata.type": item.get("@odata.type", ""),
    }


def _chunks(items: list[str], size: int) -> list[list[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]
