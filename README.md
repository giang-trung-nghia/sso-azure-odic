# sso-azure-odic

**SSO-first** playground: **Azure Entra ID (OIDC)** with two frontends and two backends. **RBAC** is intentionally small: **`admin`** and **`user`** only.

## Layout

| Path | Purpose |
| ---- | ------- |
| [`docker-compose.yml`](docker-compose.yml) | Local stack: Postgres, Redis, both APIs, both Vite apps |
| [`docs/local-infrastructure.md`](docs/local-infrastructure.md) | Ports, env vars, networking, Redis/session notes |
| [`fe-1`](fe-1) | Frontend → calls **`be-1-django`** |
| [`fe-2`](fe-2) | Frontend → calls **`be-2-fastapi`** |
| [`be-1-django`](be-1-django) | Django (+ DRF as needed): Microsoft login, OIDC, APIs for fe-1 |
| [`be-2-fastapi`](be-2-fastapi) | FastAPI: APIs for fe-2; trust Entra identity (e.g. validate JWT) |

## Goals (short)

- Single IdP (**Entra**), **OIDC** auth code flow where applicable.
- Same person can use both apps with a coherent **SSO** story (design in code: cookies vs tokens, shared domain, etc.).
- **Two roles only**: map IdP groups/app roles → **`admin`** or **`user`**.

## Local infrastructure (Docker)

Infra-only stack (Postgres, Redis, both backends, both frontends): see **[`docs/local-infrastructure.md`](docs/local-infrastructure.md)** for ports, env vars, networking, and why Redis backs Django sessions here.

```bash
cp .env.example .env   # optional
docker compose up --build
```

## Cursor / AI context

Persistent rules for the agent: **[`.cursor/rules/project-context.mdc`](.cursor/rules/project-context.mdc)** (`alwaysApply: true`).
