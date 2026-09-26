# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Command reference for the Ndorsify backend services. For architecture see
[`AGENTS.md`](AGENTS.md); for decisions see [`docs/adr/`](docs/adr/).

> The backend has been rewritten from Spring Boot to **Python/FastAPI** on
> **Postgres** ([ADR 0003](docs/adr/0003-use-python-fastapi-and-postgres.md),
> which superseded [ADR 0002](docs/adr/0002-migrate-backend-to-nodejs.md)). Each
> service is a standalone FastAPI app under `microservices/<service>/`; the
> original Java sources have been removed.

## Run everything

**Fastest path (SQLite, no Docker/Postgres):** from the workspace root, one
level up from this repo, `./start.sh` boots all 7 services plus the web
client. See `../MVP-ROADMAP.md` for what each service does.

**Docker (Postgres):** from this repo root — brings up Postgres + services.
Each container runs `alembic upgrade head` and seeds on start, so no manual
migration step is needed:

```bash
docker compose up --build
```

Swagger UI per service at `/api-docs.html`. See the ports table below.

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

## Deploying

`vercel.json` defines the repo as one Vercel project with seven services, each
routed by path (`/api/users/*` → users-service, and so on). A service-scoped
rewrite strips the prefix, so service code never sees it and nothing changes
between local and deployed.

The two internal calls are **bindings**, not public HTTP: campaign-service
receives `COLLABORATION_URL` and profile-service receives `DISCOVERY_URL`,
injected per deployment. Never hardcode a deployment hostname into either.

Everything ships together — one preview URL, one rollback for all seven. See
[ADR 0005](docs/adr/0005-deploy-as-vercel-services.md).

Environment that must be set on the project before it works: `JWT_SECRET`
(one value, all seven), `DATABASE_URL` per service, `BLOB_READ_WRITE_TOKEN`,
`SEED_ON_START=false` and `EXPOSE_DEV_TOKENS=false`.

## Ports

`users-service` 1000 · `campaign-service` 2000 · `messaging-service` 3000
(3001 in `start.sh`) · `collaboration-service` 4000 · `dynamic-content-service`
5000 (5001 in `start.sh`) · `profile-service` 6060 · `discovery-service` 9000.
Swagger UI per service at `/api-docs.html`.
