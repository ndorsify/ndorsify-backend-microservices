# 2. Migrate the backend from Spring Boot to Node.js

Date: 2026-08-24

## Status

Accepted

## Context

The backend was scaffolded as three Spring Boot 2.4.8 (Java 11) services —
`users-service`, `dynamic-content-service`, and `profile-service` — each a
standalone Maven module with in-memory H2 storage. In practice:

- The services are early-stage and share no code; there is no aggregator POM,
  no service discovery, and OpenFeign is a dependency but unused.
- The frontend is JavaScript/React. A single-language stack lowers context-switch
  cost and lets us share validation, types, and tooling across the boundary.
- The team's velocity is higher in Node than in the JVM for this product's shape
  (I/O-bound CRUD and API composition, not CPU-bound work).

## Decision

Rewrite the backend services in **Node.js**. Retain the existing service
boundaries (users, dynamic-content, profile) and their ports (1000 / 5000 / 6000)
so the contract stays familiar, and add new services per the phased feature plan.

The Java sources under `microservices/` remain as the behavioral reference until
each service reaches parity, then are removed.

## Consequences

- One language across frontend and backend; shared tooling and, potentially,
  shared types/validation.
- Existing Java details in `CLAUDE.md` / `AGENTS.md` are **transitional** — the
  stack is confirmed per service by `package.json` vs `pom.xml`.
- In-memory H2 must be replaced with a persistent datastore during the rewrite
  (see the forthcoming datastore ADR); data currently resets on restart.
- The Maven wrapper, JDK 11 requirement, and Spring specifics fall away as each
  service is ported.
