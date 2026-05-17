# fe-1 + be-1-django (session auth)

Minimal React UI to learn **Django session authentication** after Azure OIDC login.

## URLs

| App | URL |
| --- | --- |
| fe-1 | http://127.0.0.1:5171 |
| be-1-django | http://127.0.0.1:8001 |

Configure `VITE_API_URL_BE1` if the API host differs.

## Pages

| Route | Purpose |
| --- | --- |
| `/` | Login page — explains session flow; **Login with Microsoft** |
| `/dashboard` | Calls `GET /accounts/me/` with cookies; shows user or prompts login |

## Session cookie flow

1. User clicks **Login** → full navigation to  
   `http://127.0.0.1:8001/accounts/login/?next=http://127.0.0.1:5171/dashboard`
2. Django → Entra OIDC → callback → creates **Redis-backed session**.
3. Django sets **`sessionid`** cookie (host `127.0.0.1:8001`).
4. Browser returns to **`/dashboard`** on fe-1 (`next` query).
5. React runs `fetch('http://127.0.0.1:8001/accounts/me/', { credentials: 'include' })`.
6. Cookie goes to Django; Django loads session → JSON user.

## Why fe-1 does not use JWT

- **be-1-django** is the OIDC Relying Party; tokens are exchanged **server-side** at login.
- The SPA only needs proof of login: the **session cookie** on each API call.
- **fe-2** + FastAPI uses **Bearer JWT** instead (different learning path).

## CORS and credentials

Django (`settings.py`):

- `CORS_ALLOWED_ORIGINS` includes `http://127.0.0.1:5171`
- `CORS_ALLOW_CREDENTIALS = True`

fe-1 (`src/api/django.js`):

- `credentials: 'include'` on every API `fetch`

Without credentials, the browser would **not** send `sessionid` and `/accounts/me/` would return 401.

## Logout

**Logout** navigates to `http://127.0.0.1:8001/oidc/logout/` (GET allowed for local dev).

Django clears the session, then redirects through Entra logout to `DJANGO_LOGOUT_REDIRECT_URL` (default fe-1 home).

## Run

```bash
docker compose up --build
```

Open http://127.0.0.1:5171 — use the same host style (`127.0.0.1` vs `localhost`) as registered in Entra redirect URIs for Django.
