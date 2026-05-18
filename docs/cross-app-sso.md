# Cross-app SSO — fe-1 + fe-2

This guide explains **real SSO behavior** when two apps share **Azure Entra ID** but use **different authentication architectures** (Django session vs FastAPI JWT).

## Three layers of “being logged in”

| Layer | What it is | Shared across fe-1 and fe-2? |
| --- | --- | --- |
| **1. Azure / Entra SSO session** | Cookie at `login.microsoftonline.com` | **Yes** (same browser, same tenant) |
| **2. Application auth** | fe-1: Django `sessionid` + Redis · fe-2: MSAL tokens in `sessionStorage` | **No** — separate per app |
| **3. Local user row** | `accounts_userprofile.azure_oid` (Django) · `api_identities.azure_oid` (FastAPI) | **Same `oid`** after each app has logged you in |

**Centralized identity** means layer 1: one directory (Entra), one `oid` per person.

**Application sessions** are layer 2: each backend chooses how to remember the browser between requests.

## Why login often happens “only once” at Microsoft

When you open the second app and start login:

1. The app sends you to Entra (OIDC redirect or MSAL popup).
2. Entra sees an **existing SSO session** (layer 1).
3. You may get **no password prompt** (silent / account picker only).
4. Entra issues **new tokens** for that app’s client/scopes.
5. Each app **still** establishes **its own** layer-2 state (cookie or Bearer token).

So “SSO” here = **same Microsoft account, faster second login** — not a single shared cookie between `5171` and `5172`.

## Architecture diagram

```text
                    ┌─────────────────────────┐
                    │   Azure Entra ID      │
                    │   (central IdP)       │
                    │   SSO session cookie  │
                    └───────────┬─────────────┘
                                │
           ┌────────────────────┼────────────────────┐
           │                    │                    │
           ▼                    ▼                    │
    ┌──────────────┐     ┌──────────────┐            │
    │ fe-1 :5171   │     │ fe-2 :5172   │            │
    │ (React)      │     │ (React+MSAL) │            │
    └──────┬───────┘     └──────┬───────┘            │
           │ session cookie     │ Bearer JWT         │
           ▼                    ▼                    │
    ┌──────────────┐     ┌──────────────┐            │
    │ be-1-django  │     │ be-2-fastapi │            │
    │ Redis session│     │ stateless    │            │
    │ :8001        │     │ JWKS :8002   │            │
    └──────────────┘     └──────────────┘            │
           │                    │                    │
           └──────── same azure_oid ────────────────┘
                    (Postgres, separate tables)
```

## Session auth vs JWT auth (this repo)

| | **Django enterprise monolith (fe-1)** | **FastAPI stateless (fe-2)** |
| --- | --- | --- |
| **Proof on each API call** | `sessionid` cookie | `Authorization: Bearer` |
| **Server state** | Yes — session in **Redis** | No — validate JWT every time |
| **Login UX** | Full redirect via Django OIDC | MSAL popup / silent token |
| **Frontend holds** | Nothing sensitive (cookie is HttpOnly-capable*) | Access token in MSAL cache |
| **Logout** | Clears Redis session + Entra end-session URL | Clears MSAL cache + optional Entra logout |
| **Typical scale pattern** | Sticky sessions or shared Redis | Any instance + JWKS |

\*This learning app uses default session cookies; production often sets `SESSION_COOKIE_HTTPONLY = True`.

## How both systems trust the same IdP

| Check | Django (at OIDC login) | FastAPI (every request) |
| --- | --- | --- |
| Who signed the token? | ID token via JWKS (mozilla-django-oidc) | Access token via JWKS |
| Tenant | `tid` in claims / settings | `tid` must match `AZURE_AD_TENANT_ID` |
| User key | `oid` → `UserProfile.azure_oid` | `oid` → `api_identities.azure_oid` |
| Ongoing trust | Session id in cookie | JWT `exp`, `iss`, `aud`, signature |

## Manual test checklist

Use **one browser**, **localhost** consistently, stack running: `docker compose up --build`.

### Test 1 — Login order A: fe-1 first

| Step | Action | Expected |
| --- | --- | --- |
| 1 | Open http://localhost:5171/dashboard | Not signed in |
| 2 | Login with Microsoft | Entra UI → redirect back → dashboard shows user + `azure_oid` |
| 3 | Open http://localhost:5172/dashboard (new tab) | Not signed in to **fe-2** (MSAL empty) |
| 4 | Login with Microsoft on fe-2 | **Faster** Entra (often no password) — still a popup/redirect |
| 5 | Compare `azure_oid` on both dashboards | **Same value** |

### Test 2 — Login order B: fe-2 first

Reverse steps 1–5: fe-2 first, then fe-1. Same expectations.

### Test 3 — Login persistence (refresh)

| App | Action | Expected |
| --- | --- | --- |
| fe-1 | Refresh dashboard after login | Still authenticated (`/accounts/me/` 200) |
| fe-2 | Refresh dashboard after login | MSAL still has account; APIs work |

### Test 4 — Logout on one app only

| Step | Action | Expected |
| --- | --- | --- |
| 1 | Logged into **both** apps | Both show user |
| 2 | Logout on **fe-1** only | fe-1 logged out; Entra session may be cleared depending on config |
| 3 | Refresh fe-2 dashboard | May **still work** until fe-2 logout (separate MSAL cache + JWT) |
| 4 | Logout on fe-2 | fe-2 APIs fail until login again |

**Takeaway:** Logout is **per application** unless you design federated single logout across all clients.

### Test 5 — Django session expiration

In `.env` set a short session (for testing):

```bash
DJANGO_SESSION_COOKIE_AGE=300
```

Restart `be-1-django`. Log in to fe-1. Wait 5+ minutes (or set `60` for 1 minute). Refresh dashboard → `/accounts/me/` should return **401**.

fe-2 is unaffected (JWT has its own `exp`).

### Test 6 — Access token expiration (fe-2)

Access tokens are short-lived (often ~60–90 minutes; check `token_exp` on fe-2 dashboard JSON).

| Step | Action | Expected |
| --- | --- | --- |
| 1 | Note `token_exp` on fe-2 dashboard | Unix time / UI shows time left |
| 2 | Wait until expired (or revoke session in Entra for advanced tests) | `acquireTokenSilent` may popup or API returns **401** |
| 3 | Click **Refresh APIs** after MSAL renews token | Works again |

MSAL usually **refreshes** tokens silently while the Entra SSO session is valid.

### Test 7 — Entra SSO without app login

| Step | Action | Expected |
| --- | --- | --- |
| 1 | Log out of **both** apps | Both dashboards empty |
| 2 | Log in to fe-1 only | fe-1 OK |
| 3 | Open fe-2, click Login | Microsoft step is quick; fe-2 still must complete MSAL |

## Browser cookies vs tokens (cheat sheet)

| Storage | Owner | Used by |
| --- | --- | --- |
| `login.microsoftonline.com` cookies | Microsoft | Entra SSO between apps |
| `sessionid` on `localhost:8001` | Django | fe-1 → be-1-django only |
| MSAL `sessionStorage` on `5172` | MSAL library | fe-2 token cache |
| Bearer access token | Not a cookie — sent in `Authorization` header | fe-2 → be-2-fastapi |

Ports and hosts are **not** shared: `5171` ≠ `5172` ≠ `8001` ≠ `8002`.

## Correlation key: `azure_oid`

After both apps have authenticated you, compare:

- fe-1 dashboard → **azure_oid**
- fe-2 dashboard → `local.azure_oid` / `token_claims.oid`

They should match for the same Entra user. Database tables differ (`accounts_userprofile` vs `api_identities`) but the identifier is the same.

## What this repo does *not* do yet

- **Single logout** across both apps automatically
- **Shared session** between Django and FastAPI (by design — different patterns)
- **RBAC** (`admin` / `user`) — next learning step

## Quick links

| App | URL |
| --- | --- |
| fe-1 | http://localhost:5171 |
| fe-2 | http://localhost:5172 |
| Django API | http://localhost:8001/accounts/me/ |
| FastAPI API | http://localhost:8002/me |
