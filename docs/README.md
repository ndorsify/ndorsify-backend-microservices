# Ndorsify Backend — Knowledge Base

Documentation for the Ndorsify backend services. Structured so both humans and
coding agents can find the *why* behind the code, not just the *what*.

> The backend is **Python/FastAPI** on **Postgres** — see
> [ADR 0003](adr/0003-use-python-fastapi-and-postgres.md), which superseded the
> earlier Node.js decision in [ADR 0002](adr/0002-migrate-backend-to-nodejs.md).
> The original Spring Boot (Java) sources have been removed.

| Folder | Holds | Horizon |
|---|---|---|
| [`adr/`](adr/) | Architecture Decision Records | Past — decisions already made |
| [`plans/`](plans/) | PRDs & technical specifications | Future — what we intend to build |
| [`playbooks/`](playbooks/) | Runbooks & operational procedures | Present — how we operate |

See also, at the repo root:
- **`AGENTS.md`** — high-level architecture map for LLM agents.
- **`CLAUDE.md`** — command reference for coding agents.
- **`README.md`** — human developer onboarding.
