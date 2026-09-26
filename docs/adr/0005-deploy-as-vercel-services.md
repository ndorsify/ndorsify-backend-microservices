# 5. Deploy the seven services as one Vercel project

Date: 2026-09-26

## Status

Accepted

## Context

The web client is deployed; nothing behind it is. The seven FastAPI services
run only on a laptop, and the deployed SPA calls `http://localhost:1000` and
friends, so every request fails.

Three shapes were considered:

1. **Seven deployments.** No code change, then seven URLs, seven environment
   sets and seven bills forever — to protect independent release cycles that
   do not exist. One person deploys this repo.
2. **One process, seven routers mounted.** Cheapest to run, but every service
   names its package `app`, so importing all seven into one interpreter means
   renaming all seven packages and rewriting every absolute import, test
   fixture and Dockerfile command. A day of mechanical churn against working,
   tested code — to work around a module-name collision, not to solve a
   product problem.
3. **One Vercel project, seven services.** Each service keeps its own root,
   entrypoint and requirements, and builds independently — the package-name
   collision never arises, because no two of them share a process.

## Decision

Deploy the repo as a single Vercel project using Services, one per
microservice, routed by path: `/api/users/*`, `/api/campaigns/*`,
`/api/collab/*`, `/api/profiles/*`, `/api/discovery/*`, `/api/messaging/*`,
`/api/content/*`. A service-scoped rewrite strips its prefix, so no service
code changes.

The two service-to-service calls become bindings rather than public HTTP:
campaign-service gets `COLLABORATION_URL`, profile-service gets
`DISCOVERY_URL` — the same variables `clients/*.py` already read, now injected
per deployment instead of hardcoded. A service with no top-level rewrite would
be private entirely; all seven are public here because the SPA calls each of
them directly.

## Consequences

- **One deployment, one preview, one rollback** for the whole backend, and
  services are always in sync with each other.
- **The frontend gets one base URL** (`REACT_APP_API_BASE=/api`) instead of
  seven, and — proxied through the web project's own origin — the browser
  makes same-origin calls, so CORS configuration stops existing.
- **No service code changed** to get here. The boundaries, the databases and
  the JWT verification all stay as they are.
- **Everything deploys together.** Rolling back one service alone is no longer
  possible. That is the explicit trade for the operational simplicity, and it
  is the right one while one person ships all seven.
- **Deployment-time migrations still need a home.** Alembic runs in CI against
  a throwaway Postgres today ([#17](https://github.com/ndorsify/ndorsify-backend-microservices/pull/17));
  pointing it at the real database is a separate step, blocked on that database
  existing.
- **This supersedes the "mount seven routers in one app" plan** written in the
  architecture note, which was chosen before Vercel Services was considered.
  If the project ever leaves Vercel, that plan is the fallback — and the
  package rename it needs is still the only real work in it.
