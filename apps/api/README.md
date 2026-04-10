# API

This app contains the Django backend for Choir App.

## Commands

```bash
uv sync --dev
uv run python manage.py migrate --settings=config.settings.dev
uv run python manage.py runserver 0.0.0.0:8000 --settings=config.settings.dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
```
