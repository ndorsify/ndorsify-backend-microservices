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
brand ↔ creator platform. **Seven services exist today**, each a standalone
module under `microservices/`. There is **no aggregator/parent build** — no
API gateway, no shared code, no message broker; services call each other
directly over `httpx` where needed (e.g. campaign → collaboration on accept,
profile → discovery on save) and are built/run individually. See the
workspace-root [`MVP-ROADMAP.md`](../MVP-ROADMAP.md) for what's built vs. what
phase adds what next.

## Services

| Service | Port | Base path | Purpose | State |
|---|---|---|---|---|
| `users-service` | 1000 | `/auth`, `/users` | Auth (register/login/refresh/logout, verify-email, password reset), roles | Live (OAuth routes stubbed, 501) |
| `campaign-service` | 2000 | `/campaigns` | Briefs, invitations, applications, marketplace listing | Live |
| `collaboration-service` | 4000 | `/collaborations` | Deliverables, submissions, review pipeline | Live (file uploads are refs-only, no storage yet) |
| `messaging-service` | 3000 | `/conversations` | 1:1 inbox, poll-based | Live |
| `discovery-service` | 9000 | `/discovery` | Creator search/filters, shortlists, creator lookup | Live |
| `profile-service` | 6060 | `/profiles` | Creator/brand profile CRUD, completion %, pushes to discovery on save | Live (rate cards, media kit, social stats not yet built) |
| `dynamic-content-service` | 5000 | `/onboard` | Server-driven onboarding questions | Live |

Not yet built: `endorsement-service` (:7000), `payments-service` (:10000),
`notification-service` (:8000) — see phases 4/5/6 in `MVP-ROADMAP.md`.

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
- **Inter-service calls** are direct `httpx` calls authenticated with a shared
  service-to-service token (distinct from user JWTs) — e.g.
  `campaign-service` → `collaboration-service` on acceptance,
  `profile-service` → `discovery-service` on profile save. No broker, no
  gateway.

## Known issues / follow-ups

- OAuth login (`users-service`) is stubbed — routes exist but return 501.
- `collaboration-service` submissions store storage-key refs with no real
  object storage behind them yet (Phase 7 in `MVP-ROADMAP.md`).
- No lint (`ruff`/`black`) or CI beyond per-service `pytest` — see
  [phase-7](../docs/phases/phase-7-platform-hardening-launch.md).

## Guidance for new work

- Keep the existing service boundaries and ports and the established HTTP
  contracts (see the services table above).
- New services follow the phased roadmap at the workspace root
  (`MVP-ROADMAP.md` + `docs/phases/`) and reuse the layering above.

## Knowledge base

- [`docs/adr/`](docs/adr/) — architecture decisions.
- [`docs/plans/`](docs/plans/) — PRDs & tech specs (future work).
- [`docs/playbooks/`](docs/playbooks/) — operational runbooks.
