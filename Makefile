SHELL := /usr/bin/env bash

PROJECT ?= meridian-stores
NAME ?= Meridian Stores
PREFIX ?=
AWS_REGION ?= us-east-1

.PHONY: help init env backend-sync backend-test backend-dev frontend-install frontend-build frontend-dev test build ci compose-up compose-down tf-fmt tf-validate bootstrap-init bootstrap-apply aws-init aws-plan aws-apply aws-destroy clean

help:
	@printf '%s\n' \
		'Common commands:' \
		'  make init PROJECT=my-app NAME="My App" [PREFIX=MYAPP]  Initialize this template for a new project' \
		'  make env                                             Create local env files from examples if missing' \
		'  make test                                            Run backend tests and frontend build' \
		'  make compose-up                                      Build and run API + web with Docker Compose' \
		'  make compose-down                                    Stop Docker Compose services' \
		'' \
		'Backend / frontend:' \
		'  make backend-sync                                    Install backend dependencies with uv' \
		'  make backend-test                                    Run pytest' \
		'  make backend-dev                                     Start FastAPI dev server' \
		'  make frontend-install                                Install frontend dependencies with npm ci' \
		'  make frontend-build                                  Type-check and build frontend' \
		'  make frontend-dev                                    Start Vite dev server' \
		'' \
		'Terraform:' \
		'  make tf-fmt                                          Check Terraform formatting' \
		'  make tf-validate                                     Validate AWS and bootstrap Terraform' \
		'  make bootstrap-init                                  Init infra/bootstrap' \
		'  make bootstrap-apply                                 Apply infra/bootstrap' \
		'  make aws-plan TF_STATE_BUCKET=<bucket>               Plan infra/aws with remote state' \
		'  make aws-apply TF_STATE_BUCKET=<bucket>              Apply infra/aws with remote state' \
		'  make aws-destroy TF_STATE_BUCKET=<bucket>            Destroy infra/aws with remote state'

init:
	@if [[ -n "$(PREFIX)" ]]; then \
		./scripts/init-project.sh "$(PROJECT)" "$(NAME)" "$(PREFIX)"; \
	else \
		./scripts/init-project.sh "$(PROJECT)" "$(NAME)"; \
	fi

env:
	@test -f config/.env || cp config/env.example config/.env
	@test -f frontend/.env || cp frontend/config/frontend.env.example frontend/.env

backend-sync:
	cd backend && uv sync --group dev

backend-test:
	cd backend && uv run pytest

backend-dev: env backend-sync
	cd backend && set -a && source ../config/.env && set +a && uv run uvicorn meridian_stores.app:app --reload --host "$${MERIDIAN_STORES_API_HOST:-0.0.0.0}" --port "$${MERIDIAN_STORES_API_PORT:-8000}"

frontend-install:
	cd frontend && npm ci

frontend-build:
	cd frontend && npm run build

frontend-dev: env frontend-install
	cd frontend && npm run dev

test: backend-test frontend-build

build: frontend-build

ci: test tf-fmt tf-validate

compose-up: env
	docker compose --env-file ./config/.env up --build

compose-down:
	docker compose --env-file ./config/.env down

tf-fmt:
	terraform fmt -check -recursive infra

tf-validate:
	terraform -chdir=infra/aws init -backend=false
	terraform -chdir=infra/aws validate
	terraform -chdir=infra/bootstrap init -backend=false
	terraform -chdir=infra/bootstrap validate

bootstrap-init:
	terraform -chdir=infra/bootstrap init

bootstrap-apply:
	terraform -chdir=infra/bootstrap apply

aws-init:
	@test -n "$(TF_STATE_BUCKET)" || { echo 'Set TF_STATE_BUCKET=<bucket>'; exit 1; }
	cp infra/aws/backend.tf.example infra/aws/backend.tf
	terraform -chdir=infra/aws init -backend-config="bucket=$(TF_STATE_BUCKET)" -backend-config="region=$(AWS_REGION)"

aws-plan: aws-init
	terraform -chdir=infra/aws plan

aws-apply: aws-init
	terraform -chdir=infra/aws apply

aws-destroy: aws-init
	terraform -chdir=infra/aws destroy

clean:
	rm -rf frontend/dist
