# Choir App

Choir App is an MVP choir operations platform built as a modular monolith:

- `apps/api`: Django + DRF backend
- `apps/web`: Next.js frontend

The current MVP covers:

- Clerk-backed authentication
- Organizations and role-based permissions
- Members, directory, groups, and sections
- Events, RSVP tracking, and attendance
- In-app announcements
- Outbound email campaigns through Resend
- One-way Google Calendar sync from local events to Google Calendar

## Stack

- Backend: Django, Django REST Framework, PostgreSQL, pytest, Ruff, uv
- Frontend: Next.js 15, TypeScript, Tailwind CSS, Clerk, pnpm
- Local infra: Docker Compose for PostgreSQL

## Requirements

- Python 3.12
- Node.js 20+
- `uv`
- `pnpm`
- Docker / Docker Compose

## Clone

```bash
git clone https://github.com/<your-account>/choir.git
cd choir
```

## Quick Start

1. Copy env files:

   ```bash
   make setup
   ```

2. Install dependencies:

   ```bash
   make install
   ```

3. Start Postgres:

   ```bash
   make db-up
   ```

4. Update `apps/api/.env` and `apps/web/.env.local` with real credentials.

5. Apply migrations and seed sample data:

   ```bash
   make api-migrate
   make api-seed
   ```

6. Start the apps in separate terminals:

   ```bash
   make api-dev
   make web-dev
   ```

Backend: `http://127.0.0.1:8000`  
Frontend: `http://127.0.0.1:3000`

## Local Configuration

### PostgreSQL

The default local database matches `docker-compose.yml`:

```env
DATABASE_URL=postgresql://choir:choir@127.0.0.1:5432/choir
```

### Clerk

Backend in `apps/api/.env`:

```env
CLERK_JWKS_URL=https://your-clerk-domain/.well-known/jwks.json
CLERK_ISSUER=https://your-clerk-domain
CLERK_AUDIENCE=
```

Frontend in `apps/web/.env.local`:

```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=
CLERK_JWT_TEMPLATE=
```

Notes:

- `CLERK_JWT_TEMPLATE` is optional unless the backend expects a custom audience.
- If you set `CLERK_AUDIENCE` in Django, create a Clerk JWT template with that same audience and set `CLERK_JWT_TEMPLATE` in the web app.

### Resend

Set these in `apps/api/.env` to enable outbound email campaigns:

```env
COMMUNICATIONS_EMAIL_PROVIDER=resend
RESEND_API_KEY=
DEFAULT_FROM_EMAIL=Choir App <noreply@example.com>
```

### Google Calendar OAuth

Set these in `apps/api/.env`:

```env
WEB_APP_BASE_URL=http://127.0.0.1:3000
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=
GOOGLE_OAUTH_REDIRECT_URI=http://127.0.0.1:8000/api/integrations/google-calendar/oauth/callback
GOOGLE_TOKEN_ENCRYPTION_KEY=
```

Google Cloud Console setup:

1. Enable the Google Calendar API.
2. Create an OAuth client for a web application.
3. Add the exact redirect URI:

   ```text
   http://127.0.0.1:8000/api/integrations/google-calendar/oauth/callback
   ```

4. Use an admin account in the app to connect Google Calendar from `/app/<org_id>/settings/google-calendar`.

## Common Commands

```bash
make help
make setup
make install
make db-up
make api-migrate
make api-seed
make api-dev
make web-dev
make api-check
make web-check
make check
```

## Startup Notes

### Backend

`make api-dev` runs:

```bash
cd apps/api && uv run python manage.py runserver 0.0.0.0:8000 --settings=config.settings.dev
```

### Frontend

`make web-dev` runs:

```bash
cd apps/web && pnpm dev
```

The frontend talks to the Django API through `NEXT_PUBLIC_API_BASE_URL`.

## Auth Flow

1. The user signs in via Clerk in Next.js.
2. The frontend obtains a server-side Clerk token.
3. Next.js calls Django with `Authorization: Bearer <token>`.
4. Django verifies the JWT, syncs the local `User`, and resolves organization membership + permissions.

## Docs

- [docs/api-overview.md](docs/api-overview.md)
- [docs/data-model.md](docs/data-model.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/roadmap.md](docs/roadmap.md)

## Quality Checks

Backend:

```bash
make api-check
```

Frontend:

```bash
make web-check
```

Everything:

```bash
make check
```

## Git And GitHub

### Recommended branch strategy

For a solo developer, keep it simple:

- `main`: always releasable
- short-lived feature branches from `main`
- merge or rebase back into `main` quickly

Suggested branch names:

- `feat/communications-ui`
- `fix/calendar-sync-error-copy`
- `chore/repo-cleanup`

### Recommended commit style

Use a lightweight conventional style:

- `feat: add announcement compose UI`
- `fix: handle expired google refresh token`
- `docs: expand local setup notes`
- `chore: tighten gitignore and hooks`
- `refactor: simplify event audience validation`

This is enough structure for good history without adding ceremony.

### Recommended release tags

Use lightweight semver tags:

- `v0.1.0-mvp`
- `v0.1.1`
- `v0.2.0`

Use:

```bash
git tag -a v0.1.0-mvp -m "MVP release"
git push origin v0.1.0-mvp
```

### Optional pre-commit hooks

This repo includes a small `.pre-commit-config.yaml` for:

- merge-conflict detection
- trailing whitespace / EOF fixes
- YAML validation
- backend Ruff format + Ruff check

Install locally:

```bash
make pre-commit-install
```

Run manually:

```bash
make pre-commit-run
```

## CI

GitHub Actions runs:

- Django migration drift check
- Ruff lint + format check
- pytest
- frontend lint
- frontend typecheck
