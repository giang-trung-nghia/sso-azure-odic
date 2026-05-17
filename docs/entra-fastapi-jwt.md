# Microsoft Entra ID + FastAPI (`be-2-fastapi`)

This service demonstrates **stateless Bearer JWT** authentication: every protected request carries an **access token** issued by Entra; FastAPI validates it with **JWKS** and does **not** use Redis or server-side sessions.

## Bearer token flow (fe-2 → be-2-fastapi)

```text
Browser (fe-2)
  → obtains Azure access token (MSAL / Entra login in SPA — wired in a later step)
  → GET http://127.0.0.1:8002/me
      Header: Authorization: Bearer <access_token>

be-2-fastapi
  → fetch signing keys from Entra JWKS (cached)
  → verify signature (RS256), iss, aud, exp
  → verify tid matches AZURE_AD_TENANT_ID
  → read oid → upsert api_identities row (azure_oid)
  → return JSON
```

Unlike **be-1-django**, there is **no** `/oidc/callback/` on FastAPI and **no** session cookie for API auth.

## Azure-issued JWT trust model

FastAPI trusts a token only if:

| Check | What we enforce |
| --- | --- |
| **Signature** | RS256 using public keys from `https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys` |
| **Issuer (`iss`)** | `https://login.microsoftonline.com/{tenant}/v2.0` |
| **Audience (`aud`)** | `AZURE_AD_API_AUDIENCE` or `AZURE_AD_CLIENT_ID` |
| **Expiration (`exp`)** | PyJWT rejects expired tokens |
| **Tenant (`tid`)** | Must equal `AZURE_AD_TENANT_ID` |

Entra signs tokens; your API only needs the **JWKS URL** and configuration — not the client secret on each request (the secret is used when *obtaining* tokens, not when validating them).

## Why FastAPI does not need Redis-backed sessions here

- **Django (fe-1)**: browser login once → **session id cookie** → session data in Redis → `request.user` on each hit.
- **FastAPI (fe-2)**: browser (or tool) sends **Bearer token** each time → API validates JWT → no server session store required.

That is the common **stateless API** pattern: horizontal scaling is simple because any instance can validate the token independently.

## Django session auth vs FastAPI JWT auth (this repo)

| | **be-1-django** | **be-2-fastapi** |
| --- | --- | --- |
| Proof of identity | `sessionid` cookie | `Authorization: Bearer …` |
| Storage | Redis session + Postgres user | Postgres `api_identities` only |
| Login UX | Redirect to Entra (OIDC code flow) | Client obtains token (MSAL later) |
| Same person | `accounts_userprofile.azure_oid` | `api_identities.azure_oid` (same `oid` claim) |

Both map the stable Entra **`oid`** claim locally; RBAC (`admin` / `user`) is a later step.

## Endpoints

| Method | Path | Auth |
| --- | --- | --- |
| `GET` | `/health` | Public |
| `GET` | `/me` | Bearer required |
| `GET` | `/protected` | Bearer required |

## Environment variables

Uses the same `.env` as Django for tenant and client id (see `.env.example`):

- `AZURE_AD_TENANT_ID`
- `AZURE_AD_CLIENT_ID`
- `AZURE_AD_API_AUDIENCE` (optional; defaults to client id)
- `POSTGRES_*` (compose sets `POSTGRES_HOST=postgres`)

## Manual test (Azure CLI)

Request an access token whose **resource/audience** matches your API app, then call the API:

```bash
# Replace TENANT and CLIENT_ID; audience must match AZURE_AD_CLIENT_ID or AZURE_AD_API_AUDIENCE
az login --tenant "$AZURE_AD_TENANT_ID"
TOKEN=$(az account get-access-token --resource "$AZURE_AD_CLIENT_ID" --query accessToken -o tsv)

curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8002/me | jq
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8002/protected | jq
```

If validation fails with **audience** errors, expose a dedicated API app registration or set `AZURE_AD_API_AUDIENCE` to the `aud` value inside your token (decode at [jwt.ms](https://jwt.ms) for learning).

## Cross-app SSO (preview)

**SSO** across fe-1 and fe-2 means the **same Entra account** signs in once at the IdP; each app still uses its own mechanism (Django session vs Bearer token). A shared `azure_oid` in both databases lets you correlate users; true single cookie across both backends is not required for this learning layout.
