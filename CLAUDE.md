# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Command reference for the Ndorsify backend services. For architecture see
[`AGENTS.md`](AGENTS.md); for decisions see [`docs/adr/`](docs/adr/).

> The backend has been rewritten from Spring Boot to **Python/FastAPI** on
> **Postgres** ([ADR 0003](docs/adr/0003-use-python-fastapi-and-postgres.md),
> which superseded [ADR 0002](docs/adr/0002-migrate-backend-to-nodejs.md)). Each
> service is a standalone FastAPI app under `microservices/<service>/`; the
> original Java sources have been removed.

## Run everything (Docker)

From the repo root — brings up Postgres (three databases) + all three services.
Each container runs `alembic upgrade head` and seeds on start, so no manual
migration step is needed:

```bash
docker compose up --build
```

Services: `users-service` :1000 · `dynamic-content-service` :5000 ·
`profile-service` :6000. Swagger UI per service at `/api-docs.html`.

## Run a single service (Python / FastAPI)

Requires **Python 3.9+**. Each service is standalone — run from inside a single
service directory (`microservices/<service>/`):

```bash
python3 -m venv .venv && source .venv/bin/activate   # one-time
pip install -r requirements.txt                      # install deps
python -m app.server                                 # run (uvicorn on the service port)
pytest -q                                             # run tests (uses SQLite, no DB needed)
pytest -q tests/test_users.py::test_update_existing_and_missing  # single test
```

Configuration is via environment (or a local `.env`, see `.env.example`):
`PORT` and `DATABASE_URL` (SQLAlchemy async URL, e.g.
`postgresql+asyncpg://ndorsify:ndorsify@localhost:5432/usersdb`). Without a
Postgres running, point `DATABASE_URL` at SQLite for local poking, e.g.
`sqlite+aiosqlite:///dev.sqlite3`.

There is **no aggregator build** — services share no code and are built/run
individually. Loop over `microservices/*` or use `docker compose`.

## Datastore & migrations

Postgres via SQLAlchemy 2.0 async (`asyncpg`); one database per service. Schema
is owned by **Alembic** — `docker compose` runs `alembic upgrade head` before
each service starts. On SQLite (local poking / tests) tables are created
directly via `create_all`, so no migration step is needed there.

```bash
cd microservices/<service>
alembic upgrade head                          # apply migrations (uses DATABASE_URL)
alembic revision --autogenerate -m "message"  # author a new migration after model changes
alembic downgrade -1                          # roll back one revision
```

`dynamic-content-service` seeds reference rows on startup (idempotent); seeding
is separate from migrations.

## Ports

`users-service` 1000 · `dynamic-content-service` 5000 · `profile-service` 6000.
Swagger UI per service at `/api-docs.html`.
