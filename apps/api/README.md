# API

This app contains the Django backend for Choir App.

## Local Commands

```bash
uv sync --dev
uv run python manage.py makemigrations --settings=config.settings.dev
uv run python manage.py makemigrations --check --dry-run --settings=config.settings.test
uv run python manage.py migrate --settings=config.settings.dev
uv run python manage.py seed_sample_data --settings=config.settings.dev
uv run python manage.py runserver 0.0.0.0:8000 --settings=config.settings.dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Local Environment

Copy:

```bash
cp apps/api/.env.example apps/api/.env
```

Important integrations:

- Clerk for authentication
- PostgreSQL for local development
- Resend for outbound email campaigns
- Google Calendar OAuth for one-way event sync

The backend loads `apps/api/.env` by default from `manage.py`.

## Seed Data

`seed_sample_data` creates a sample organization with:

- admin, section leader, and member users
- member profiles and groups
- sample events, RSVPs, and attendance
- sample announcements
- sample message campaigns

The command is intended to be idempotent for repeated local use.

## Auth Notes

Protected routes expect:

```http
Authorization: Bearer <clerk-jwt>
```

Django verifies the Clerk token and syncs the local `User` record from token claims.

