# Architecture

## Overview

Choir App starts as a modular monolith with a Django backend and a Next.js frontend in the same repository. The backend owns domain logic, persistence, validation, and future permission rules. The frontend consumes the backend through a small API client layer and should stay focused on presentation and interaction.

## Principles

- Keep domain logic out of React components.
- Keep permission checks centralized in backend modules and policies.
- Prefer backend-first domain modules over frontend-led feature slices.
- Keep the event model separate from Google Calendar integration so bidirectional sync can be added later without polluting core scheduling concepts.
- Avoid premature infrastructure layers, service boundaries, and generic abstractions.

## Repository Shape

- `apps/api`: Django project, REST API, and future domain modules
- `apps/web`: Next.js app, typed API client, and UI
- `docs`: living architecture and product notes
- `infra`: reserved for future infrastructure assets when they are justified

## API Boundary

The Django app exposes REST endpoints under `/api`. The web app should call those endpoints through `src/lib/api/*` rather than sprinkling fetch logic across components.

## Multi-Tenant Readiness

The initial scaffold does not implement tenancy, but the codebase is structured to add organization-scoped modules later. Tenant boundaries should be enforced in backend services and permissions, not inferred in the UI.
