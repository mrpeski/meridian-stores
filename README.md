# Meridian Stores

A **minimal** FastAPI + Vite/React AWS starter: one JSON endpoint, one static page, and **environment-driven** configuration end to end (local dev, Docker Compose, Terraform, and GitHub Actions CI/CD).

**Coding agents (Cursor, CI assistants, etc.):** see [`AGENTS.md`](./AGENTS.md) for repo layout, API/frontend conventions, copy-paste commands, and what to update when you change behavior or configuration.

## What you get

- **Backend** (`backend/`): `GET /health`, `GET /api/hello` — same middleware ordering idea as the main app (exception handlers first, CORS last).
- **Frontend** (`frontend/`): calls `apiUrl("/api/hello")` — dev uses the Vite proxy; production/CI sets **`VITE_API_BASE_URL`** to API Gateway (see `frontend/src/lib/apiBase.ts`).
- **Config** (`config/env.example`): shared `MERIDIAN_STORES_*` knobs for the API process.
- **Infra** (`infra/`): AWS-ready Terraform for Lambda/API Gateway/ECR/S3/CloudFront, bootstrap Terraform for state + GitHub OIDC, optional nginx override example, and Docker Compose.
- **CI/CD** (`.github/workflows/`): CI, deploy, and manual destroy workflows.
- **Makefile** (`Makefile`): one command surface for local dev, tests, Docker Compose, Terraform, and template initialization.

For AWS setup, required GitHub variables/secrets, deploy, and teardown, see [DEPLOY.md](./DEPLOY.md).

## Rename the project

For a new project, run the template initializer first:

```bash
./scripts/init-project.sh my-project "My Project"
```

Or with `make`:

```bash
make init PROJECT=my-project NAME="My Project"
```

By default, the initializer derives the environment/CI variable prefix from the slug, so `my-project` becomes `MY_PROJECT_*`. To choose it explicitly, pass a third argument, or set `PREFIX` with `make`:

```bash
./scripts/init-project.sh my-project "My Project" MYAPP
make init PROJECT=my-project NAME="My Project" PREFIX=MYAPP
```

That rewrites the template's environment and CI variable prefix to the chosen prefix, for example `MYAPP_*`. The rewrite covers backend settings, Docker/Compose variables, GitHub Actions variables/secrets, Terraform examples, and docs. Python package imports stay as `hello_world` so the starter keeps working without a module rename.

Then change **`PROJECT_NAME`** in `config/.env` (copy from `config/env.example`) if needed. That value:

- Sets the **Docker Compose project name** when you pass the same file to Compose (see below).
- Drives the API **defaults** for FastAPI title (`app_name`), JSON `service` (`{PROJECT_NAME}-svc`), and the hello line (`Hello from {PROJECT_NAME}.`) unless you set the optional `MERIDIAN_STORES_APP_NAME`, `MERIDIAN_STORES_SERVICE_NAME`, or `MERIDIAN_STORES_HELLO_MESSAGE` overrides.

Match Terraform by setting **`project_name`** in `infra/terraform/terraform.tfvars` (see `terraform.tfvars.example`); default image tags in outputs become `{project_name}-api:local` and `{project_name}-web:local` when you leave the image variables empty.

## Common commands

```bash
make help
make env
make backend-test
make frontend-build
make test
make compose-up
make compose-down
```

For AWS:

```bash
make bootstrap-init
make bootstrap-apply
make aws-plan TF_STATE_BUCKET=<state-bucket>
make aws-apply TF_STATE_BUCKET=<state-bucket>
make aws-destroy TF_STATE_BUCKET=<state-bucket>
```

## Quick start (local)

```bash
cp config/env.example config/.env
cd backend && uv sync
uv run uvicorn hello_world.app:app --reload --host "${MERIDIAN_STORES_API_HOST:-0.0.0.0}" --port "${MERIDIAN_STORES_API_PORT:-8000}"
```

In another shell:

```bash
cp frontend/config/frontend.env.example frontend/.env
cd frontend && npm install && npm run dev
```

Open the printed dev URL (defaults to port **5173**). The UI calls `/api/hello` via the proxy target from `VITE_API_PROXY_TARGET`.

Equivalent Makefile flow:

```bash
make env
make backend-dev
make frontend-dev
```

## Configuration reference

### API (`PROJECT_NAME` + `MERIDIAN_STORES_*`)

Loaded from process environment and, if present, `config/.env` then `backend/.env.local` / `backend/.env` (see `backend/src/hello_world/settings.py`).

| Variable | Default | Purpose |
| --- | --- | --- |
| `PROJECT_NAME` | `meridian-stores` | Primary rename slug; also accepted as `MERIDIAN_STORES_PROJECT_NAME` |
| `MERIDIAN_STORES_API_HOST` | `0.0.0.0` | Uvicorn bind address |
| `MERIDIAN_STORES_API_PORT` | `8000` | Uvicorn port |
| `MERIDIAN_STORES_CORS_ORIGINS` | `http://localhost:5173` | Comma-separated origins, or `*` |
| `MERIDIAN_STORES_APP_NAME` | *(derived)* | FastAPI title; defaults to `PROJECT_NAME` |
| `MERIDIAN_STORES_SERVICE_NAME` | *(derived)* | JSON `service`; defaults to `{PROJECT_NAME}-svc` |
| `MERIDIAN_STORES_HELLO_MESSAGE` | *(derived)* | `message` in `/api/hello`; defaults to `Hello from {PROJECT_NAME}.` |

### Frontend dev server (`VITE_*`)

| Variable | Default | Purpose |
| --- | --- | --- |
| `VITE_API_PROXY_TARGET` | `http://127.0.0.1:8000` | Vite `/api` proxy target |
| `VITE_DEV_HOST` | `0.0.0.0` | Dev server bind |
| `VITE_DEV_PORT` | `5173` | Dev server port |
| `VITE_PREVIEW_PORT` | same as dev | `vite preview` port |
| `VITE_API_BASE_URL` | *(unset)* | API Gateway origin for production builds (no trailing slash) |
| `VITE_CLERK_PUBLISHABLE_KEY` | *(unset)* | Optional; baked in at build time if you use Clerk in the SPA |

### GitHub Actions

CI/CD is included under **`.github/workflows/`**:

- `ci.yml` runs backend tests, frontend build, and Terraform validation.
- `deploy-aws.yml` is manual-only and deploys the AWS stack after you run it from GitHub Actions.
- `destroy-aws.yml` is manual-only and destroys the AWS application stack after you type `DESTROY`.

See [DEPLOY.md](./DEPLOY.md) for the bootstrap steps and the exact GitHub variables/secrets to add.

### Docker Compose (shell / `.env` next to `docker-compose.yml`)

| Variable | Default | Purpose |
| --- | --- | --- |
| `PROJECT_NAME` | `meridian-stores` | Compose **project name** (set in `config/.env` and pass with `--env-file`) |
| `MERIDIAN_STORES_CONFIG_ENV` | `./config/.env` | Path passed to `env_file` for the API service |
| `MERIDIAN_STORES_API_PORT_PUBLISH` | `8000` | Published host port for the API |
| `MERIDIAN_STORES_API_PORT` | `8000` | In-container port (must match image `CMD`) |
| `MERIDIAN_STORES_WEB_PORT_PUBLISH` | `5173` | Published host port for nginx |

Copy `config/env.example` → `config/.env` before first `docker compose up` so `env_file` exists.

```bash
cp config/env.example config/.env
docker compose --env-file ./config/.env up --build
```

Equivalent Makefile flow:

```bash
make compose-up
make compose-down
```

`--env-file ./config/.env` makes Compose read `PROJECT_NAME` (and any other compose-time vars you add) for interpolation in `docker-compose.yml`.

### Terraform

`infra/terraform/` defines **variables and outputs only** — plug them into your own modules (EKS, Cloud Run, etc.). Set **`project_name`** once; example values live in `infra/terraform/terraform.tfvars.example`.

### AWS

`infra/aws/` provisions **ECR, Lambda (container), HTTP API Gateway, S3 website, CloudFront**. See **`infra/aws/README.md`**. The included deploy workflow handles first-time ECR creation, linux/amd64 image build/push, Terraform apply, SPA build, S3 sync, and CloudFront invalidation.

## Tests

```bash
cd backend && uv sync --group dev && uv run pytest
```

Or:

```bash
make test
```
