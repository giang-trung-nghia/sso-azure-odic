# Local infrastructure

This document describes the **Docker Compose** stack only: wiring, ports, environment variables, and why **PostgreSQL** and **Redis** exist. **No Azure OIDC and no application auth** are implemented in this step.

## Monorepo layout

```text
sso-azure-odic/
├── docker-compose.yml      # Orchestrates all local services on one Docker network
├── .env.example            # Copy to `.env` and adjust publish ports if needed
├── docs/
│   └── local-infrastructure.md
├── fe-1/                   # React (Vite) → calls be-1-django (later)
├── fe-2/                   # React (Vite) → calls be-2-fastapi (later)
├── be-1-django/            # Django + DRF (session path; Redis-backed sessions when REDIS_HOST is set)
└── be-2-fastapi/           # FastAPI (JWT path later; CORS only for now)
```

## Ports (defaults)

| Service | URL on your machine | Container port | Notes |
|--------|---------------------|------------------|--------|
| **fe-1** | http://127.0.0.1:5171 | 5171 | Vite dev server |
| **fe-2** | http://127.0.0.1:5172 | 5172 | Vite dev server |
| **be-1-django** | http://127.0.0.1:8001 | 8001 | Gunicorn |
| **be-2-fastapi** | http://127.0.0.1:8002 | 8002 | Uvicorn |
| **postgres** | `localhost:5433` | 5432 | Host **5433** by default to reduce clashes with a local Postgres on 5432 |
| **redis** | `localhost:6379` | 6379 | Same port inside and outside by default |

Health endpoints (for probes and manual checks):

- Django: `GET http://127.0.0.1:8001/health/`
- FastAPI: `GET http://127.0.0.1:8002/health`

## Docker networking

All services attach to the Compose network **`appnet`**. Inside the network, DNS names match **service names**:

- `postgres`, `redis`, `be-1-django`, `be-2-fastapi`, `fe-1`, `fe-2`

So from **be-1-django**, the database host is **`postgres`** and Redis is **`redis`** (not `127.0.0.1`). Your **browser** on the host still uses **`127.0.0.1`** (or `localhost`) with the **publish** ports above.

## Environment variable strategy

1. **`.env` at the repo root** — loaded by Docker Compose for substitution and passed into containers where `docker-compose.yml` references `${VAR}`.
2. **`.env.example`** — committed template; copy to `.env` and change secrets/ports for your machine.
3. **Service-specific variables** — grouped by prefix: `POSTGRES_*`, `REDIS_*`, `DJANGO_*`, `FASTAPI_*`, `VITE_*` (for future frontend API base URLs).

Do not commit `.env` (it is gitignored).

## Why Redis is in this architecture

Redis is a **fast, external datastore** used here as preparation for **shared, server-side state** that must outlive a single web process:

- **Django session store** (this repo): when `REDIS_HOST` is set, sessions are stored in Redis via `django-redis`, so multiple Gunicorn workers (and later multiple containers) see the **same** session data.
- **Cross-cutting patterns** you will see in larger systems: rate limits, OIDC nonce/state stores, logout lists, etc. often use Redis. We only wire sessions here to keep the step small.

## Why Django uses Redis-backed sessions (for learning)

**Problem**: default Django sessions use the **database**. That works for one process, but in a **production-like** setup you commonly run **several Gunicorn workers** or **several replicas**. You want session reads/writes to be **consistent and fast** across all of them.

**Redis-backed sessions** move session payload to **Redis** while the browser still only holds the **session cookie**. That matches the “enterprise monolith” path in this learning repo: **OIDC login will happen later**; today we only establish **where** session data will live.

If you run Django **without** `REDIS_HOST` (e.g. local `runserver`), settings fall back to **database sessions** and a local SQLite DB so you can iterate without Docker.

## Commands

From the repository root:

```bash
cp .env.example .env   # optional: then edit ports/secrets
docker compose up --build
```

Stop with `Ctrl+C` or `docker compose down` (add `-v` to remove the Postgres volume).

## Troubleshooting

### Frontends: port mapping works but browser gets nothing / wrong port

Vite must **listen on `0.0.0.0`** inside the container (not only `127.0.0.1`) so Docker can forward host traffic. Ports must match the compose mapping (**5171** / **5172**).

Do **not** run `pnpm run dev -- --host …` via Docker `CMD` for this repo: pnpm expands that to `vite -- --host …`, and the extra `--` confuses the CLI so Vite can fall back to the default port (**5173**). The fix is **`server.host` / `server.port` in `vite.config.js`** (already set) plus plain `pnpm run dev` in the Dockerfile.

## What is intentionally not in this step

- No Azure Entra ID / OIDC configuration.
- No login flows, JWT issuance, or permission checks beyond Django’s defaults.
- FastAPI only exposes `/` and `/health` plus optional CORS for **fe-2** origins.

Next steps in the learning path: add OIDC to Django, then JWT validation in FastAPI, then map **`admin` / `user`** RBAC from Entra claims.
