SHELL := /bin/bash

.PHONY: api-install web-install db-up db-down api-migrate api-dev web-dev api-test api-lint api-format-check web-lint web-typecheck check

api-install:
	cd apps/api && uv sync --dev

web-install:
	cd apps/web && pnpm install

db-up:
	docker compose up -d db

db-down:
	docker compose down

api-migrate:
	cd apps/api && uv run python manage.py migrate --settings=config.settings.dev

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
	cd apps/web && pnpm exec tsc --noEmit

check: api-lint api-format-check api-test web-lint web-typecheck
