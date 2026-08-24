# Ndorsify Backend — Knowledge Base

Documentation for the Ndorsify backend services. Structured so both humans and
coding agents can find the *why* behind the code, not just the *what*.

> The backend is being rewritten from Spring Boot (Java) to Node.js — see
> [ADR 0002](adr/0002-migrate-backend-to-nodejs.md). Confirm a service's current
> stack by `package.json` vs `pom.xml` before acting.

| Folder | Holds | Horizon |
|---|---|---|
| [`adr/`](adr/) | Architecture Decision Records | Past — decisions already made |
| [`plans/`](plans/) | PRDs & technical specifications | Future — what we intend to build |
| [`playbooks/`](playbooks/) | Runbooks & operational procedures | Present — how we operate |

See also, at the repo root:
- **`AGENTS.md`** — high-level architecture map for LLM agents.
- **`CLAUDE.md`** — command reference for coding agents.
- **`README.md`** — human developer onboarding.
