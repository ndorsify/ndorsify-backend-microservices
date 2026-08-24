# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Command reference for the Ndorsify backend services. For architecture see
[`AGENTS.md`](AGENTS.md); for decisions see [`docs/adr/`](docs/adr/).

> The backend is being rewritten from Spring Boot to Node.js
> ([ADR 0002](docs/adr/0002-migrate-backend-to-nodejs.md)). Use the command set
> that matches a service's current stack — check for `package.json` (Node) vs
> `pom.xml` (Java).

## Current (Java / Maven) — reference implementation

Requires **JDK 11**. If `java -version` fails, install one first (e.g.
`brew install --cask temurin@11`). Each service is standalone — run these **from
inside a single service directory** (`microservices/<service>/`):

```bash
./mvnw spring-boot:run                            # run this service
./mvnw test                                       # run all tests
./mvnw test -Dtest=UsersServiceApplicationTests   # single test class
./mvnw test -Dtest='ClassName#methodName'         # single test method
./mvnw clean package                              # build the jar (add -DskipTests to skip tests)
./mvnw dependency:resolve                         # download deps only
```

There is **no aggregator POM** — you cannot build all services with one command.
Loop over `microservices/*` or run each individually.

## After the Node.js rewrite

Per-service commands will move to `package.json` scripts (to be defined during
the rewrite), e.g. `npm install`, `npm run dev`, `npm test`. Update this section
as each service is ported.

## Ports

`users-service` 1000 · `dynamic-content-service` 5000 · `profile-service` 6000
(also in `config-details/Ports.txt`). Swagger UI per service at `/api-docs.html`.
