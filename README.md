# Choir App

Choir App is a production-oriented choir management scaffold built as a modular monolith. The repository starts with a Django REST API, a Next.js web app, local PostgreSQL via Docker Compose, and enough project tooling to keep the first vertical slices clean.

## Stack

- Backend: Django, Django REST Framework, PostgreSQL, pytest, Ruff, uv
- Frontend: Next.js 15, TypeScript, Tailwind CSS, shadcn/ui, pnpm
- Local infrastructure: Docker Compose for PostgreSQL

## Required Local Installs

Install these before running the project locally:

- Python 3.12
- Node.js 20+ (or another version supported by Next.js 15)
- `pnpm`
- `uv`
- Docker and Docker Compose

Suggested install references:

- Python: `pyenv` or your system package manager
- Node.js: `nvm`, `fnm`, or the official installer
- `pnpm`: `npm install --global pnpm`
- `uv`: https://docs.astral.sh/uv/getting-started/installation/
- Docker: https://docs.docker.com/get-docker/

## Repository Layout

```text
.
├── apps/
│   ├── api/    # Django REST API and future business modules
│   └── web/    # Next.js application
├── docs/       # Architecture notes and product roadmap
├── infra/      # Reserved for future infrastructure artifacts
├── docker-compose.yml
└── Makefile
```

## Environment Setup

1. Copy the example env files:

   ```bash
   cp apps/api/.env.example apps/api/.env
   cp apps/web/.env.example apps/web/.env.local
   ```

2. Start PostgreSQL:

   ```bash
   make db-up
   ```

3. Install API dependencies:

   ```bash
   make api-install
   ```

4. Install web dependencies:

   ```bash
   make web-install
   ```

Because `uv` and `pnpm` were not available in the scaffolding environment, the lockfiles are generated when you run those install commands locally.

## Running The API

Apply migrations:

```bash
make api-migrate
```

Start the Django development server:

```bash
make api-dev
```

The API runs on `http://127.0.0.1:8000`.

Health endpoints:

- `GET /api/health/live`
- `GET /api/health/ready`

## Running The Web App

Start the Next.js dev server:

```bash
make web-dev
```

The web app runs on `http://127.0.0.1:3000`.

## Quality Checks

Run backend tests:

```bash
make api-test
```

Run backend lint and format checks:

```bash
make api-lint
make api-format-check
```

Run frontend lint and typecheck:

```bash
make web-lint
make web-typecheck
```

Run everything:

```bash
make check
```

## Notes

- The repository is intentionally light on business modules in the first milestone.
- Future multi-tenant concerns should be implemented in backend modules and policies, not in React components.
- Google Calendar sync, payments, ticketing, and other deferred features are documented in [docs/roadmap.md](docs/roadmap.md).
