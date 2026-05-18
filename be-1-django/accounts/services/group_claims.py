"""
Extract Azure AD group object IDs from OIDC claims (inline or overage).
"""

from __future__ import annotations

import logging
from typing import Any

import requests

LOGGER = logging.getLogger(__name__)


def extract_group_object_ids(claims: dict[str, Any], access_token: str | None) -> list[str]:
    """
    Return unique group GUIDs from token claims.

    Handles:
    - `groups`: list of object IDs in token/userinfo
    - `_claim_names` / `_claim_sources`: group overage (fetch from endpoint)
    """
    groups = claims.get("groups")
    if isinstance(groups, list) and groups:
        return _dedupe_guids(groups)

    claim_names = claims.get("_claim_names") or {}
    claim_sources = claims.get("_claim_sources") or {}
    if "groups" in claim_names and access_token:
        source = claim_sources.get("groups") or {}
        endpoint = source.get("endpoint")
        if endpoint:
            try:
                return _fetch_overage_group_ids(endpoint, access_token)
            except requests.RequestException as exc:
                LOGGER.warning("Failed to fetch overage groups: %s", exc)

    return []


def _dedupe_guids(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        guid = str(value).strip()
        if guid and guid not in seen:
            seen.add(guid)
            result.append(guid)
    return result


def _fetch_overage_group_ids(endpoint: str, access_token: str) -> list[str]:
    response = requests.get(
        endpoint,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict) and "groups" in payload:
        return _dedupe_guids(payload["groups"])
    if isinstance(payload, list):
        return _dedupe_guids(payload)
    return []
