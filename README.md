# sso-azure-odic

**SSO-first** playground: **Azure Entra ID (OIDC)** with two frontends and two backends. **RBAC** is intentionally small: **`admin`** and **`user`** only.

## Layout

| Folder | Purpose |
| ------ | ------- |
| [`fe-1`](fe-1) | Frontend → calls **`be-1-django`** |
| [`fe-2`](fe-2) | Frontend → calls **`be-2-fastapi`** |
| [`be-1-django`](be-1-django) | Django (+ DRF as needed): Microsoft login, OIDC, APIs for fe-1 |
| [`be-2-fastapi`](be-2-fastapi) | FastAPI: APIs for fe-2; trust Entra identity (e.g. validate JWT) |

## Goals (short)

- Single IdP (**Entra**), **OIDC** auth code flow where applicable.
- Same person can use both apps with a coherent **SSO** story (design in code: cookies vs tokens, shared domain, etc.).
- **Two roles only**: map IdP groups/app roles → **`admin`** or **`user`**.

## Cursor / AI context

Persistent rules for the agent: **[`.cursor/rules/project-context.mdc`](.cursor/rules/project-context.mdc)** (`alwaysApply: true`).
