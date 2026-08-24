# AGENTS.md — Ndorsify Backend

High-level architecture map for LLM agents. For commands see [`CLAUDE.md`](CLAUDE.md);
for the "why" behind decisions see [`docs/adr/`](docs/adr/).

> **Stack is in transition.** The services are being rewritten from Spring Boot
> (Java 11) to **Node.js** — see [ADR 0002](docs/adr/0002-migrate-backend-to-nodejs.md).
> The Java details below describe the current reference implementation; confirm a
> service's live stack by `package.json` vs `pom.xml` before acting.

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
| `profile-service` | 6000 | — | Profiles | Skeleton (no controllers yet) |

Ports are also recorded in `config-details/Ports.txt`.

## Patterns (current Java reference — carry the intent into Node)

- **Layering:** `controller/` → `service/` → `repository/`, with `entity/` for
  persistence and `dto/request` + `dto/response` at the API boundary. Entity↔DTO
  mapping is done by static methods in a `util/` class, not a mapping framework.
- **Response envelope:** `dynamic-content-service` wraps responses in a generic
  `NDorsifyUtil<T>` (`status` / `message` / `data`); `users-service` returns DTOs
  directly. No shared library — copy-pasted per service if reused.
- **Persistence:** in-memory **H2** (`jdbc:h2:mem:...`) — data resets on restart;
  `dynamic-content-service` seeds from `src/main/resources/data.sql`. Replacing
  this with a persistent datastore is a required step of the rewrite.
- **Docs:** each service exposes Swagger UI at `/api-docs.html` (springdoc).
- `spring-cloud-starter-openfeign` is a dependency in every service but **no Feign
  clients exist yet** — services don't call each other. Inter-service calls become
  HTTP clients in the Node rewrite.

## Known issues

- `dynamic-content-service`'s `application.properties` sets
  `spring.application.name=users-service` (copy-paste error).

## Rewrite guidance

- Keep the existing service boundaries and ports (1000 / 5000 / 6000).
- Introduce a persistent datastore (next ADR) — do not carry over in-memory H2.
- New services follow the phased feature plan (kept at the workspace root).

## Knowledge base

- [`docs/adr/`](docs/adr/) — architecture decisions.
- [`docs/plans/`](docs/plans/) — PRDs & tech specs (future work).
- [`docs/playbooks/`](docs/playbooks/) — operational runbooks.
