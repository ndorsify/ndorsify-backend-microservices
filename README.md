# Ndorsify Backend

The backend services for **Ndorsify** — a platform connecting brands with
creators/influencers for endorsements, campaigns, and marketing engagement. The
web client lives in `ndorsify-app`.

> **Rewritten to Python/FastAPI on Postgres.** See
> [ADR 0003](docs/adr/0003-use-python-fastapi-and-postgres.md) (amends
> [ADR 0002](docs/adr/0002-migrate-backend-to-nodejs.md)). The original Spring
> Boot (Java 11) sources under `microservices/*/src/` remain only as the
> behavioral reference until removed.

## Services

| Service | Port | Purpose |
|---|---|---|
| `users-service` | 1000 | User CRUD with pagination |
| `dynamic-content-service` | 5000 | Server-driven onboarding questions |
| `profile-service` | 6060 | Profiles (skeleton) |

Each service is a standalone FastAPI app under `microservices/`. There is no
combined build — run and build them individually, or use Docker Compose.

## Run everything (Docker)

```bash
docker compose up --build
```

Brings up Postgres (three databases: `usersdb` / `dynamiccontentdb` /
`profiledb`) and all three services. Each container runs `alembic upgrade head`
and seeds on start — no manual migration step needed. Swagger UI per service at
`/api-docs.html`.

## Run a single service

Requires **Python 3.9+**.

```bash
cd microservices/users-service
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.server        # uvicorn on the service port
```

Configure via `.env` (copy `.env.example`): `PORT` and `DATABASE_URL` (a
SQLAlchemy async URL). Point `DATABASE_URL` at Postgres for real use, or SQLite
(`sqlite+aiosqlite:///dev.sqlite3`) for quick local poking.

## Test

```bash
cd microservices/<service>
pytest -q
```

Tests run against a throwaway SQLite database (via `aiosqlite`), so no Postgres
is required to run the suite.

## Documentation

- [`AGENTS.md`](AGENTS.md) — architecture map (for AI agents and new devs).
- [`CLAUDE.md`](CLAUDE.md) — command reference for coding agents.
- [`docs/`](docs/) — knowledge base: [ADRs](docs/adr/), [plans](docs/plans/),
  [playbooks](docs/playbooks/).
