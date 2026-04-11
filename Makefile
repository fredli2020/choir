SHELL := /bin/bash

.PHONY: help install setup db-up db-down db-logs api-install web-install api-migrate api-makemigrations api-makemigrations-check api-seed api-check api-dev web-dev api-test api-lint api-format-check web-lint web-typecheck web-check pre-commit-install pre-commit-run check

help:
	@printf "\nChoir App commands:\n"
	@printf "  make setup                    Copy local env files if missing\n"
	@printf "  make install                  Install API and web dependencies\n"
	@printf "  make db-up                    Start local Postgres\n"
	@printf "  make api-migrate              Run Django migrations (dev settings)\n"
	@printf "  make api-seed                 Seed sample data (dev settings)\n"
	@printf "  make api-dev                  Start Django dev server\n"
	@printf "  make web-dev                  Start Next.js dev server\n"
	@printf "  make api-check                Run backend checks\n"
	@printf "  make web-check                Run frontend checks\n"
	@printf "  make pre-commit-install       Install local Git hooks\n"
	@printf "  make pre-commit-run           Run pre-commit on all files\n"
	@printf "  make check                    Run all checks\n\n"

setup:
	test -f apps/api/.env || cp apps/api/.env.example apps/api/.env
	test -f apps/web/.env.local || cp apps/web/.env.example apps/web/.env.local

install: api-install web-install

api-install:
	cd apps/api && uv sync --dev

web-install:
	cd apps/web && pnpm install

db-up:
	docker compose up -d db

db-down:
	docker compose down

db-logs:
	docker compose logs -f db

api-makemigrations:
	cd apps/api && uv run python manage.py makemigrations --settings=config.settings.dev

api-makemigrations-check:
	cd apps/api && uv run python manage.py makemigrations --check --dry-run --settings=config.settings.test

api-migrate:
	cd apps/api && uv run python manage.py migrate --settings=config.settings.dev

api-seed:
	cd apps/api && uv run python manage.py seed_sample_data --settings=config.settings.dev

api-dev:
	cd apps/api && uv run python manage.py runserver 0.0.0.0:8000 --settings=config.settings.dev

web-dev:
	cd apps/web && pnpm dev

api-test:
	cd apps/api && uv run pytest

api-lint:
	cd apps/api && uv run ruff check .

api-format-check:
	cd apps/api && uv run ruff format --check .

web-lint:
	cd apps/web && pnpm lint

web-typecheck:
	cd apps/web && pnpm typecheck

api-check: api-makemigrations-check api-lint api-format-check api-test

web-check: web-lint web-typecheck

pre-commit-install:
	uvx pre-commit install

pre-commit-run:
	uvx pre-commit run --all-files

check: api-check web-check
