# fe-1 + be-1-django (session auth)

Minimal React UI to learn **Django session authentication** after Azure OIDC login.

## URLs

| App | URL |
| --- | --- |
| fe-1 | http://localhost:5171 |
| be-1-django | http://localhost:8001 |

Configure `VITE_API_URL_BE1` if the API host differs.

## Pages

| Route | Purpose |
| --- | --- |
| `/` | Login page — explains session flow; **Login with Microsoft** |
| `/dashboard` | Calls `GET /api/me/` with cookies; shows user or prompts login |

## Session cookie flow

1. User clicks **Login** → full navigation to  
   `http://localhost:8001/accounts/login/?next=http://localhost:5171/dashboard`
2. Django → Entra OIDC → callback → creates **Redis-backed session**.
3. Django sets **`sessionid`** cookie (host `localhost:8001`).
4. Browser returns to **`/dashboard`** on fe-1 (`next` query).
5. React runs `fetch('http://localhost:8001/api/me/', { credentials: 'include' })`.
6. Cookie goes to Django; Django loads session → JSON user.

## Why fe-1 does not use JWT

- **be-1-django** is the OIDC Relying Party; tokens are exchanged **server-side** at login.
- The SPA only needs proof of login: the **session cookie** on each API call.
- **fe-2** + FastAPI uses **Bearer JWT** instead (different learning path).

## CORS and credentials

Django (`settings.py`):

- `CORS_ALLOWED_ORIGINS` includes `http://localhost:5171`
- `CORS_ALLOW_CREDENTIALS = True`

fe-1 (`src/api/django.js`):

- `credentials: 'include'` on every API `fetch`

Without credentials, the browser would **not** send `sessionid` and `/api/me/` would return 401.

### Troubleshooting: login works but `/api/me/` returns 401

1. **Use localhost everywhere** — fe-1, Django API, and Entra redirect URI must all use `http://localhost` (not `127.0.0.1`). Entra registration: `http://localhost:8001/oidc/callback/`.
2. **Cross-port cookies** — fe-1 (`:5171`) and Django (`:8001`) are different sites. Settings use `SESSION_COOKIE_SAMESITE=None` and `SESSION_COOKIE_SECURE=1` so `fetch` can send `sessionid`.
3. **Rebuild** after changing `.env`: `docker compose up --build be-1-django fe-1`
4. In DevTools → Application → Cookies → `http://localhost`, confirm `sessionid` exists after login.

## Logout

**Logout** navigates to `http://localhost:8001/oidc/logout/` (GET allowed for local dev).

Django clears the session, then redirects through Entra logout to `DJANGO_LOGOUT_REDIRECT_URL` (default fe-1 home).

## Run

```bash
docker compose up --build
```

Open http://localhost:5171 — same host as Entra’s Django redirect URI (`http://localhost:8001/oidc/callback/`).
