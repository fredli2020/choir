# API

This app contains the Django backend for Choir App.

## Commands

```bash
uv sync --dev
uv run python manage.py makemigrations --settings=config.settings.dev
uv run python manage.py migrate --settings=config.settings.dev
uv run python manage.py seed_sample_data --settings=config.settings.dev
uv run python manage.py runserver 0.0.0.0:8000 --settings=config.settings.dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Auth Notes

Protected API routes expect a Clerk JWT in the `Authorization: Bearer <token>` header. The backend verifies the JWT against Clerk JWKS and syncs the local `User` identity from token claims.
