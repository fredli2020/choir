# Choir App

Choir App is a production-oriented choir management scaffold built as a modular monolith. The repository currently includes a Django REST API foundation for authentication, organizations, and centralized RBAC permissions, plus a Next.js web app that will consume that API.

## Stack

- Backend: Django, Django REST Framework, PostgreSQL, pytest, Ruff, uv
- Frontend: Next.js 15, TypeScript, Tailwind CSS, shadcn/ui, pnpm
- Local infrastructure: Docker Compose for PostgreSQL
- Frontend auth provider: Clerk

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

2. Fill in the Clerk backend auth settings in `apps/api/.env`:

   ```env
   CLERK_JWKS_URL=https://your-clerk-domain/.well-known/jwks.json
   CLERK_ISSUER=https://your-clerk-domain
   CLERK_AUDIENCE=
   ```

3. Fill in the Clerk frontend auth settings in `apps/web/.env.local`:

   ```env
   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
   CLERK_SECRET_KEY=
   CLERK_JWT_TEMPLATE=
   ```

   Notes:
   - `CLERK_JWT_TEMPLATE` is optional when Django accepts the default Clerk session token.
   - If `CLERK_AUDIENCE` is set in `apps/api/.env`, create a Clerk JWT template with the same audience and set `CLERK_JWT_TEMPLATE` to that template name in `apps/web/.env.local`.

4. Start PostgreSQL:

   ```bash
   make db-up
   ```

5. Install API dependencies:

   ```bash
   make api-install
   ```

6. Install web dependencies:

   ```bash
   make web-install
   ```

## Running The API

Apply migrations:

```bash
make api-migrate
```

Seed a sample organization with three sample users and roles:

```bash
cd apps/api && /home/fred/.local/bin/uv run python manage.py seed_sample_data --settings=config.settings.dev
```

Start the Django development server:

```bash
make api-dev
```

The API runs on `http://127.0.0.1:8000`.

### Auth Contract

The frontend signs users in with Clerk and sends the Clerk session token to Django as a Bearer token.

Example request headers:

```http
Authorization: Bearer <clerk-session-jwt>
```

Protected endpoints added in this milestone:

- `GET /api/me`
- `GET /api/me/organizations`
- `GET /api/me/context?organization_id=<uuid>`
- `GET /api/orgs/<org_id>/membership`
- `GET /api/orgs/<org_id>/permissions`

Health endpoints:

- `GET /api/health/live`
- `GET /api/health/ready`

## Running The Web App

Start the Next.js dev server:

```bash
make web-dev
```

The web app runs on `http://127.0.0.1:3000`.

Primary frontend routes:

- `/` landing page
- `/sign-in` Clerk sign-in surface
- `/sign-up` Clerk sign-up surface
- `/app` authenticated app entry that resolves the current organization
- `/app/<org_id>` organization dashboard
- `/app/<org_id>/members` staff member records
- `/app/<org_id>/directory` directory-safe member view
- `/app/<org_id>/events` event and RSVP surface
- `/app/<org_id>/profile` linked member profile surface

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

## Auth Flow

1. The user signs in through Clerk in the Next.js app.
2. The Next.js app uses Clerk server helpers to mint a token for backend API calls.
3. The web app calls Django with `Authorization: Bearer <token>` from server-rendered routes.
4. Django verifies the JWT against Clerk JWKS and issuer configuration.
5. Django creates or updates the local `User` identity record from Clerk claims.
6. Django resolves `OrganizationMembership` for org-scoped routes and calculates centralized permissions.
7. The API responds with current-user, org-context, and permission data the frontend can use.

## Notes

- The repository is intentionally light on choir business modules beyond auth and org foundations in this milestone.
- `User` is the login identity only. Future choir member records should live in a separate `MemberProfile`-style domain model.
- Future multi-tenant concerns should be enforced in backend modules and policies, not in React components.
- Google Calendar sync, payments, ticketing, and other deferred features are documented in [docs/roadmap.md](docs/roadmap.md).
