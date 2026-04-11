# Web

This app contains the Next.js frontend for Choir App.

## Local Commands

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
```

## Local Environment

Copy:

```bash
cp apps/web/.env.example apps/web/.env.local
```

Required values:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=
CLERK_JWT_TEMPLATE=
```

## App Shape

The frontend is intentionally thin:

- server-rendered app shell
- small API client layer in `src/lib/api`
- organization-aware routes under `/app/[orgId]`
- admin Google Calendar connection page under `/app/[orgId]/settings/google-calendar`

The frontend should keep domain logic in Django services rather than React components.

