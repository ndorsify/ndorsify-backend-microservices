# AGENTS.md — Ndorsify Backend

High-level architecture map for LLM agents. For commands see [`CLAUDE.md`](CLAUDE.md);
for the "why" behind decisions see [`docs/adr/`](docs/adr/).

> **Stack:** the services are **Python/FastAPI** on **Postgres** (SQLAlchemy 2.0
> async) — see [ADR 0003](docs/adr/0003-use-python-fastapi-and-postgres.md),
> which superseded the earlier Node.js decision in
> [ADR 0002](docs/adr/0002-migrate-backend-to-nodejs.md). The original Spring
> Boot (Java 11) sources have been removed; the ADRs retain the history.

## What this is

The Ndorsify backend: independently-deployable services behind a two-sided
brand ↔ creator platform. Three services exist today, each a standalone module
under `microservices/`. There is **no aggregator/parent build** — services do
not share code and are built/run individually.

## Services

| Service | Port | Base path | Purpose | State |
|---|---|---|---|---|
| `users-service` | 1000 | `/users` | User CRUD with pagination/sorting | Live |
| `dynamic-content-service` | 5000 | `/onboard/creator` | Server-driven onboarding questions | Live |
| `profile-service` | 6060 | — | Profiles | Skeleton (health only, no routes yet) |

## Patterns (Python/FastAPI)

Each service is a standalone FastAPI app under `microservices/<service>/app/`:

- **Layering:** `routers/` (controllers) → `services/` (business logic) →
  `repositories/` (SQLAlchemy data access), with `models/` for ORM entities and
  `schemas/` for Pydantic DTOs. Entity↔DTO mapping lives in `utils/mapping.py`
  (plain functions, mirroring the Java `util/` classes).
- **Config:** `app/core/config.py` — `pydantic-settings` reads `PORT` and
  `DATABASE_URL` from the environment / `.env`.
- **DB wiring:** `app/db/session.py` holds the async engine, session factory,
  and the `get_session` FastAPI dependency. On Postgres the schema is owned by
  **Alembic** (`alembic/`, run via `alembic upgrade head` before the server
  starts — see each Dockerfile); on SQLite (local/tests) `init_db` creates
  tables directly. Seeding (where applicable) runs on startup and is idempotent.
- **Response envelope:** `dynamic-content-service` wraps responses in a generic
  `NDorsifyUtil` (`status` / `message` / `data`, `schemas/envelope.py`);
  `users-service` returns DTOs directly and uses a Spring-`Page`-shaped envelope
  (`schemas/pagination.py`) for paginated `GET /users`. No shared library —
  each service is self-contained.
- **Persistence:** **Postgres** via SQLAlchemy 2.0 async + `asyncpg`; one DB per
  service. `dynamic-content-service` seeds onboarding rows in `app/db/seed.py`
  (port of the Java `data.sql`). Tests run against SQLite (`aiosqlite`).
- **Docs:** each service exposes Swagger UI at `/api-docs.html` (FastAPI
  `docs_url`), plus a `/health` endpoint.
- Services don't call each other yet. Inter-service calls become HTTP clients
  (e.g. `httpx`) when needed.

## Known issues / follow-ups

- `users-service` and `dynamic-content-service` have an initial Alembic
  migration (`0001_initial`); `profile-service` has the Alembic scaffolding but
  no migration yet (no models). Author its first migration when the profile
  model lands (`alembic revision --autogenerate`).

## Guidance for new work

- Keep the existing service boundaries and ports (1000 / 5000 / 6060) and the
  established HTTP contracts.
- New services follow the phased feature plan (kept at the workspace root) and
  reuse the layering above.

## Knowledge base

- [`docs/adr/`](docs/adr/) — architecture decisions.
- [`docs/plans/`](docs/plans/) — PRDs & tech specs (future work).
- [`docs/playbooks/`](docs/playbooks/) — operational runbooks.
