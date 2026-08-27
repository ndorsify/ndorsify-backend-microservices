# Technical Specifications — Phase 1 (Marketplace)

Implementation specs for each group of items in the workspace-root
`PHASE-1-TODO.md`. Read alongside the [Feature Plan](https://claude.ai/code/artifact/e08c9f98-f24e-4c83-a708-709747d35dd5)
and [ADR 0003](../../adr/0003-use-python-fastapi-and-postgres.md).

| Spec | Covers | Service(s) | Port |
|---|---|---|---|
| [p0-foundation](p0-foundation.md) | Auth, roles, profiles, base messaging & discovery | users, profile, messaging, discovery | 1000/6000/3000/9000 |
| [e1-campaigns](e1-campaigns.md) | Briefs, invitations, marketplace, applications | campaign | 2000 |
| [e2-outreach](e2-outreach.md) | Templates, campaign-linked threads | messaging | 3000 |
| [e3-collaboration](e3-collaboration.md) | Deliverables, status pipeline, submissions | collaboration | 4000 |
| [e4-endorsements](e4-endorsements.md) | Endorsement requests, two-way reviews | endorsement | 7000 |
| [e5-notifications](e5-notifications.md) | Event bus, in-app + email | notification | 8000 |
| [e6-profiles-discovery](e6-profiles-discovery.md) | Socials, media kit, brand directory | profile, discovery | 6000/9000 |
| [e7-platform](e7-platform.md) | Media storage, verification, search, CI, **CORS** | cross-cutting | — |

> **Frontend specs** live in the `ndorsify-app` repo under the same path
> (`docs/plans/technical-specifications/`): `ui-foundation` and `p0-ui`. The SPA
> requires **CORS on every service** — see [e7-platform §5](e7-platform.md).

## Shared conventions (all specs assume these)

- **Stack:** FastAPI · SQLAlchemy 2.0 async (`asyncpg`) · Pydantic v2 · Alembic ·
  one Postgres database per service. Tests: `pytest` on SQLite (`aiosqlite`).
- **Service shape:** `app/{routers,services,repositories,models,schemas,utils,core,db}`
  per the [scaffold checklist](../../../../PHASE-1-TODO.md).
- **IDs:** UUID (`uuid4`) primary keys on all new tables. Timestamps: `created_at`,
  `updated_at` (server default `now()`), plus soft-delete `is_deleted` where the
  Java reference used it.
- **Cross-service references** are stored as bare UUIDs (e.g. `brand_id`,
  `creator_id`, `campaign_id`) — **no cross-database foreign keys**. Integrity is
  enforced in the service layer, not the DB.
- **Auth:** every non-public endpoint expects a Bearer JWT (see
  [p0-foundation](p0-foundation.md)); the decoded `user_id` + `role` arrive via a
  shared FastAPI dependency.
- **Envelope:** list endpoints return the `Page`-shaped pagination schema; content
  endpoints may use the `NDorsifyUtil` envelope (both already in the codebase).
- **Events:** producers `POST` to the notification-service ingest endpoint
  (see [e5-notifications](e5-notifications.md)); no broker in Phase 1.
