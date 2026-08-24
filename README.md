# Ndorsify Backend

The backend services for **Ndorsify** — a platform connecting brands with
creators/influencers for endorsements, campaigns, and marketing engagement. The
web client lives in `ndorsify-app`.

> **Being rewritten to Node.js.** The current services are Spring Boot (Java 11)
> and serve as the behavioral reference. See
> [ADR 0002](docs/adr/0002-migrate-backend-to-nodejs.md).

## Services

| Service | Port | Purpose |
|---|---|---|
| `users-service` | 1000 | User CRUD with pagination |
| `dynamic-content-service` | 5000 | Server-driven onboarding questions |
| `profile-service` | 6000 | Profiles (skeleton) |

Each service is standalone under `microservices/`. There is no combined build —
run and build them individually.

## Prerequisites (current Java stack)

- **JDK 11.** If not installed: `brew install --cask temurin@11`.
- Maven wrapper is bundled per service (`./mvnw`) — no separate Maven install.

## Run a service

```bash
cd microservices/users-service
./mvnw spring-boot:run
```

Each service exposes Swagger UI at `/api-docs.html`. Storage is in-memory H2, so
**data resets on every restart** (this changes during the Node rewrite).

## Common commands

| Command (run inside a service dir) | What it does |
|---|---|
| `./mvnw spring-boot:run` | Run the service |
| `./mvnw test` | Run tests |
| `./mvnw clean package` | Build the jar |

See [`CLAUDE.md`](CLAUDE.md) for the full command reference, including single-test
runs and post-rewrite Node commands.

## Documentation

- [`AGENTS.md`](AGENTS.md) — architecture map (for AI agents and new devs).
- [`CLAUDE.md`](CLAUDE.md) — command reference for coding agents.
- [`docs/`](docs/) — knowledge base: [ADRs](docs/adr/), [plans](docs/plans/),
  [playbooks](docs/playbooks/).
