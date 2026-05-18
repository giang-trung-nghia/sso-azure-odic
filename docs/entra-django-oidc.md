# Microsoft Entra ID + Django (`be-1-django`)

This document explains how OIDC login is wired for **`be-1-django`**, what the tokens mean, and why Django still uses **server-side sessions** after Azure authenticates the user.

## Prerequisites (Azure Portal)

Create an **App registration** (single tenant is fine for learning).

1. **Authentication → Platform configurations → Web**
2. Add a **Redirect URI** that matches what Django will send to Entra during the code exchange. For local Docker defaults, register:

   `http://localhost:8001/oidc/callback/`

   Notes:

   - The path is **`/oidc/callback/`** (mozilla-django-oidc default; not `odic`).
   - Entra commonly accepts **`localhost`** for local redirect URIs; use **`localhost` everywhere** (fe-1, Django API, Entra registration)—do not mix with `127.0.0.1`.

3. Create a **client secret** (Certificates & secrets).

4. Copy **Application (client) ID**, **Directory (tenant) ID**, and the secret into your `.env` (see `.env.example`).

### Optional: logout redirect

If Entra rejects your logout redirect, add the same URL you use for `DJANGO_LOGOUT_REDIRECT_URL` / `ENTRA_POST_LOGOUT_REDIRECT_URI` under the app’s **Front-channel logout URL** / allowed post-logout redirects (wording varies by portal version).

### Optional: `groups` claim

Entra often **does not** put security groups directly into tokens for large memberships (“overage”). For learning, treat `groups` as **best-effort**:

- Token optional claims / app roles (later RBAC step), or
- Microsoft Graph (`/memberOf`, etc.)

The `/accounts/claims/` endpoint shows what Django last saw in the merged claim snapshot.

## Environment variables

See repo **`.env.example`**. The important ones are:

| Variable | Purpose |
| --- | --- |
| `AZURE_AD_TENANT_ID` | Entra tenant GUID (or `common` / `organizations` for special cases) |
| `AZURE_AD_CLIENT_ID` | App registration client id |
| `AZURE_AD_CLIENT_SECRET` | App registration client secret |
| `DJANGO_LOGOUT_REDIRECT_URL` | Where to send the browser after Entra logout completes |
| `OIDC_RP_SCOPES` | OAuth scopes requested at authorize time (defaults include `openid email profile offline_access`) |

If tenant/client id/secret are **missing**, `OIDC_ENABLED` is false: Django boots for infra work, and `/accounts/login/` returns **503** JSON explaining what to configure.

## Endpoints (Django)

| URL | Purpose |
| --- | --- |
| `GET /accounts/login/` | Starts OIDC login (redirects to `/oidc/authenticate/`) |
| `GET /oidc/authenticate/` | mozilla-django-oidc: redirect browser to Entra authorize endpoint |
| `GET /oidc/callback/` | mozilla-django-oidc: handles authorization `code`, exchanges for tokens, logs user into Django |
| `GET/POST /oidc/logout/` | Ends Django session and redirects to Entra logout (GET enabled for local learning via `ALLOW_LOGOUT_GET_METHOD`) |
| `GET /accounts/me/` | JSON: current user + `azure_oid` (requires login) |
| `GET /accounts/claims/` | JSON: `oid` / `tid` / `email` / `groups` snapshot stored at login (requires login) |

## Authorization code flow (what happens in the browser)

This is the OIDC/OAuth2 **authorization code** flow (simplified):

1. User visits **`/accounts/login/`** → Django redirects to **`/oidc/authenticate/`**.
2. Django redirects the browser to Entra’s **authorize** URL with `response_type=code`, `client_id`, `redirect_uri`, `scope`, `state`, and (here) **PKCE** parameters.
3. User signs in at Microsoft. Entra validates MFA / policies as configured.
4. Entra redirects the browser back to Django at **`/oidc/callback/?code=...&state=...`**.
5. Django (server-side) exchanges the **`code`** at Entra’s **token** endpoint for tokens, validates the **ID token**, loads **userinfo** (Graph), then creates/updates the Django user and **logs the user in**.
6. Django issues a **session cookie** pointing at **Redis-backed session data**.

**ID token (`id_token`)**: a JWT minted by Entra meant for **your client** (`aud` is usually your app’s client id). It asserts “who signed in” and carries stable identifiers like **`oid`** and tenant **`tid`**.

**Access token (`access_token`)**: a token meant for **calling APIs** (often Microsoft Graph). mozilla-django-oidc uses it to call **`https://graph.microsoft.com/oidc/userinfo`** by default in this repo.

By default we **do not** store raw tokens in the session (`OIDC_STORE_ACCESS_TOKEN` / `OIDC_STORE_ID_TOKEN` are off). Enable them only when you intentionally need them (e.g., Graph calls).

## Why Django still uses sessions after OIDC login

OIDC proves identity **once** at login time. After that, your app still needs a stable, efficient way to recognize the browser on each request.

Django’s pattern is:

- **Browser** holds only the **session id** cookie.
- **Server** stores session payload in **Redis** (configured in `settings.py` when `REDIS_HOST` is set).

That keeps the browser from holding long-lived identity JWTs for every API call in this Django app, and it matches common “web app behind OIDC” deployments.

## Local user mapping (`azure_oid`)

We keep a small `accounts.UserProfile` row keyed by Entra **`oid`** (stored as `azure_oid`) linked to `auth.User`.

- Django **`User.username`** is derived as `entra_<oid>` (stable, unique).
- Django **`User.email`** is populated from claims when present.
- The password is always **unusable** (`set_unusable_password()`): authentication is delegated to Entra.

## Operational notes

- Use **`http://localhost:8001`** (and open fe-1 at **`http://localhost:5171`**) so the redirect URI, session cookies, and Entra registration all match.
- Start login with a **top-level navigation** (a normal link) to avoid third-party cookie issues while iterating locally.
