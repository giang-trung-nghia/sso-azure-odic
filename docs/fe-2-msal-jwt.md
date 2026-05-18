# fe-2 + be-2-fastapi (MSAL + Bearer JWT)

Minimal React UI to learn **stateless JWT** authentication with Microsoft Entra ID and FastAPI.

## URLs

| App | URL |
| --- | --- |
| fe-2 | http://127.0.0.1:5172 |
| be-2-fastapi | http://127.0.0.1:8002 |

## Entra app registration (SPA)

In addition to the Django **Web** redirect URI, add a **Single-page application** platform:

| Setting | Value |
| --- | --- |
| Redirect URI | `http://127.0.0.1:5172` |

Enable **Expose an API** (if not already):

1. Application ID URI: `api://{client-id}`
2. Add a scope (e.g. `access_as_user`) — optional if you use `.default`

Grant the SPA permission to its own API scope (API permissions → your app → delegated).

### Scope and audience

fe-2 requests tokens with scope (default):

`api://{client-id}/.default`

FastAPI validates `aud` against `AZURE_AD_CLIENT_ID` or `AZURE_AD_API_AUDIENCE`. If `/me` returns 401, decode the token at [jwt.ms](https://jwt.ms) and align `VITE_AZURE_API_SCOPE` / `AZURE_AD_API_AUDIENCE` with the token `aud` claim.

Override scope in `.env`:

```bash
VITE_AZURE_API_SCOPE=api://your-client-id/.default
```

## Pages

| Route | Purpose |
| --- | --- |
| `/` | Login + JWT vs session comparison |
| `/dashboard` | MSAL account, `GET /me`, `GET /protected` with Bearer token |

## Token acquisition

1. User clicks **Login with Microsoft**.
2. **MSAL** (`@azure/msal-browser`) runs `loginPopup` against Entra.
3. Entra returns tokens; MSAL stores them in **sessionStorage** (tab-scoped cache).
4. Before API calls, `acquireTokenSilent` (or popup fallback) gets a fresh **access token** for the API scope.

fe-2 does **not** implement the authorization code flow itself — MSAL does, in the browser.

## Token storage

| What | Where |
| --- | --- |
| Access token (for API) | MSAL cache → `sessionStorage` |
| Refresh token | MSAL internal cache (not used manually) |
| ID token | MSAL cache (profile display; not sent to FastAPI) |

Closing the tab clears sessionStorage. This is different from fe-1’s **HttpOnly session cookie** on the Django host.

## Bearer token requests

```javascript
fetch('http://127.0.0.1:8002/me', {
  headers: { Authorization: `Bearer ${accessToken}` },
})
```

- **No** `credentials: 'include'` (no Django session cookie).
- FastAPI validates JWT on every request (signature, iss, aud, exp, tid).
- CORS allows `http://127.0.0.1:5172` without cookies.

## Compare fe-1 vs fe-2

| | fe-1 + Django | fe-2 + FastAPI |
| --- | --- | --- |
| Login UX | Redirect to Django → Entra | MSAL popup → Entra |
| Proof to API | `sessionid` cookie | `Authorization: Bearer` |
| API state | Redis session | None (stateless) |
| Same Entra user | `accounts_userprofile.azure_oid` | `api_identities.azure_oid` |

## Environment

Root `.env` (used by docker-compose for fe-2):

- `AZURE_AD_TENANT_ID` → `VITE_AZURE_TENANT_ID`
- `AZURE_AD_CLIENT_ID` → `VITE_AZURE_CLIENT_ID`
- `VITE_API_URL_BE2`
- Optional `VITE_AZURE_API_SCOPE`

## Run

```bash
docker compose up --build
```

Open http://127.0.0.1:5172 → Login → Dashboard → verify `/me` and `/protected` JSON.
