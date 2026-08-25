# 3. Rewrite the backend in Python/FastAPI on Postgres

Date: 2026-08-24

## Status

Accepted (supersedes [ADR 0002](0002-migrate-backend-to-nodejs.md))

## Context

[ADR 0002](0002-migrate-backend-to-nodejs.md) accepted a rewrite from Spring Boot
to **Node.js**, primarily to unify the language with the JavaScript/React
frontend. On revisiting the decision before starting the port, we chose
**Python/FastAPI** for the backend instead. The services are I/O-bound CRUD and
API-composition work; FastAPI gives first-class async, Pydantic validation, and
auto-generated OpenAPI docs with very little ceremony, and the team is productive
in Python. The single-language-with-frontend benefit from ADR 0002 is
consciously traded away for this.

The datastore question left open by ADR 0002 is also settled here: in-memory H2
is replaced with **Postgres**, accessed via **SQLAlchemy 2.0 (async)** with the
`asyncpg` driver. (Prisma, floated informally, is Node-specific and does not
apply to a Python stack.)

## Decision

- Rewrite all three services (`users-service`, `dynamic-content-service`,
  `profile-service`) in **Python 3 + FastAPI**, served by **uvicorn**.
- Keep the existing service boundaries and ports (1000 / 5000 / 6000) and the
  existing HTTP contracts (paths, request/response shapes, the `NDorsifyUtil`
  envelope, a Spring-`Page`-shaped envelope for paginated users).
- Persist data in **Postgres** via **SQLAlchemy 2.0 async** + `asyncpg`; one
  database per service (`usersdb` / `dynamiccontentdb` / `profiledb`).
- Preserve the Swagger UI path: FastAPI serves docs at `/api-docs.html`.
- Per-service layering mirrors the Java intent: `routers/` (controllers) →
  `services/` → `repositories/`, with `models/` (ORM) and `schemas/` (Pydantic
  DTOs), and entity↔DTO mapping in `utils/`.

## Consequences

- **Supersedes the Node.js decision** in ADR 0002; the "one language across FE
  and BE" rationale no longer holds — frontend stays JS/React, backend is Python.
- Per-service tooling is now `pip install -r requirements.txt`, `uvicorn`,
  and `pytest` (see [`CLAUDE.md`](../../CLAUDE.md)). A root `docker-compose.yml`
  brings up Postgres + all three services.
- Schema on Postgres is owned by **Alembic**: each service has an `alembic/`
  setup and `docker compose` runs `alembic upgrade head` before starting the
  service. `users-service` and `dynamic-content-service` ship an initial
  migration; `profile-service` has the scaffolding but no migration yet (no
  models). On SQLite (local/tests) tables are created via `create_all`, so the
  suite needs no migration step.
- Tests run against SQLite (`aiosqlite`) so the suite needs no live Postgres,
  while production runs on Postgres — the SQLAlchemy models are portable across
  both.
- The Java sources under `microservices/*/src/` remain as the behavioral
  reference and should be removed once the Python services are confirmed at
  parity in review.
