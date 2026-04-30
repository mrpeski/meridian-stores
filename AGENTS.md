# Agent guide — Meridian Stores

This repo is a **minimal** FastAPI + React AWS starter: **FastAPI** (`backend/`), **Vite + React** (`frontend/`), **shared env** (`config/`), optional **Docker Compose** at the root, and **Terraform** examples under `infra/`. Treat `README.md` as the source of truth for variable names and defaults.

## Layout

| Path | Role |
| --- | --- |
| `backend/src/hello_world/` | FastAPI app (`app.py`), Pydantic settings (`settings.py`) |
| `backend/tests/` | Pytest |
| `frontend/src/` | SPA; API base URL logic in `lib/apiBase.ts` |
| `config/env.example` | Copy to `config/.env` for local / Compose |
| `frontend/config/frontend.env.example` | Copy to `frontend/.env` for Vite dev |
| `infra/terraform/` | Variables + outputs only (no cloud resources in-tree) |
| `infra/aws/` | Full AWS example (ECR, Lambda, API Gateway, S3, CloudFront) |
| `.github/workflows/` | CI (YAML under repo root only; GitHub ignores nested `.github/`) |

## Conventions to preserve

- **API middleware order**: Register exception handlers first; add **CORS last** (outermost), matching the established app pattern (`backend/src/hello_world/app.py`).
- **Configuration**: Everything is **environment-driven**. Backend loads `PROJECT_NAME` / `MERIDIAN_STORES_*` from process env, then `config/.env`, then `backend/.env.local` / `backend/.env` (see `settings.py`). Do not hardcode deployment-specific URLs or names in application code.
- **Frontend**: Dev uses the Vite proxy to the API; production builds use **`VITE_API_BASE_URL`** (no trailing slash) when set.

## Commands (from repo root unless noted)

**Backend**

```bash
cp config/env.example config/.env
cd backend && uv sync && uv run uvicorn hello_world.app:app --reload --host 0.0.0.0 --port 8000
```

**Backend tests**

```bash
cd backend && uv sync --group dev && uv run pytest
```

**Frontend**

```bash
cp frontend/config/frontend.env.example frontend/.env
cd frontend && npm install && npm run dev
```

**Docker Compose** (needs `config/.env` for `env_file` and optional `--env-file ./config/.env` for `PROJECT_NAME`)

```bash
docker compose --env-file ./config/.env up --build
```

**Lambda image** (when touching deploy): build with `backend/Dockerfile.lambda` for **linux/amd64** before `aws lambda update-function-code` (see `infra/aws/README.md`).

## When changing behavior

- If you add API routes or change JSON shape, update **`frontend/`** callers and **`backend/tests/`**.
- If you add env vars, extend **`config/env.example`**, document them in **`README.md`**, and wire them through **`settings.py`** (or Vite `VITE_*` / `frontend.env.example`) as appropriate.
- Infra or CI secrets: follow existing naming (`MERIDIAN_STORES_*` in workflows); do not commit real values.

## What not to do

- Do not commit `config/.env`, `frontend/.env`, or `backend/.env*` with secrets.
- Avoid large refactors unrelated to the task; this starter stays intentionally small.
