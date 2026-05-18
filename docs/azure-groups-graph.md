# Azure groups + Microsoft Graph (be-1-django)

After Entra login, Django extracts **group object IDs** from OIDC claims, stores them in PostgreSQL (many-to-many), resolves **display names** via **Microsoft Graph**, and exposes everything on **`GET /api/me/`**.

## Why object IDs, not names?

| Token (OIDC) | Directory (Graph) |
| --- | --- |
| Small, stable GUIDs (`groups` claim) | `displayName`, `description`, `mail`, flags |
| Same ID even if group is renamed | Authoritative metadata |

## Group overage

If a user belongs to **many** groups, Entra may omit the inline `groups` array and instead emit:

- `_claim_names` → `"groups"`
- `_claim_sources.groups.endpoint` → URL to download the full ID list

`accounts.services.group_claims` fetches that URL with the login **access token**.

If there are **no** group claims at all, sync falls back to Graph:

`GET /v1.0/me/memberOf/microsoft.graph.group`

## Identity claims vs local RBAC

| Layer | This step | Later |
| --- | --- | --- |
| **Identity** | `oid`, `tid`, `email`, group memberships | — |
| **Local RBAC** | Not assigned | Map groups → `admin` / `user` |

## Database model

```text
User 1──1 AzureUserProfile *──* AzureGroup
```

- **`AzureUserProfile`**: `azure_oid`, `tenant_id`, `email`, …
- **`AzureGroup`**: `object_id` (unique), `display_name`, Graph metadata
- **M2M**: one user → many groups (not simplified to a single group)

## Entra configuration

1. **API permissions** (delegated): `GroupMember.Read.All` (or `Group.Read.All`)
2. **Grant admin consent**
3. **Token configuration** (optional): add `groups` optional claim to ID / access token
4. **`.env`**:

```bash
OIDC_RP_SCOPES=openid email profile offline_access GroupMember.Read.All
OIDC_STORE_ACCESS_TOKEN=1
```

5. Log in again (sync runs on each successful OIDC login)

## API

`GET http://localhost:8001/api/me/` (session cookie; also available at `/accounts/api/me/`)

Response includes:

- `azure_oid`, `tenant_id`, `email`
- `groups[]` with `object_id`, `display_name`, …
- `group_object_ids`, `group_display_names` (convenience arrays)

Legacy: `GET /accounts/me/` returns the same payload.

## Code layout

| Path | Role |
| --- | --- |
| `accounts/models.py` | `AzureUserProfile`, `AzureGroup`, M2M |
| `accounts/services/group_claims.py` | Parse inline + overage group IDs |
| `accounts/services/graph_groups.py` | Graph `getByIds`, `/groups/{id}`, `memberOf` |
| `accounts/services/group_sync.py` | Persist + resolve on login |
| `accounts/backends.py` | Calls `sync_user_groups` after OIDC login |
| `accounts/views.py` | `api_me` |
| `fe-1` dashboard | Displays groups table |

## Enterprise mapping

| Learning repo | Typical production |
| --- | --- |
| Sync on login | Async job / nightly SCIM sync |
| Graph per login | Cached directory with TTL |
| `AzureGroup` table | Identity store / read model |
| `/api/me` | Profile BFF endpoint |
