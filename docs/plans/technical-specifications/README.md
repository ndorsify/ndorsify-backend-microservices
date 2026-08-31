# Technical Specifications

Implementation specs for each backend epic. The workspace-root
[`MVP-ROADMAP.md`](../../../../MVP-ROADMAP.md) is the source of truth for
**status** and **build order** (phases 0–7, in `../../../../docs/phases/`) —
these specs hold the API/data-model detail each phase links to.

| Spec | Covers | Service(s) | Port | Status |
|---|---|---|---|---|
| [p0-foundation](p0-foundation.md) | Auth, roles, profiles, base messaging & discovery | users, profile, messaging, discovery | 1000/6060/3000/9000 | ✅ Implemented (OAuth stubbed) |
| [e1-campaigns](e1-campaigns.md) | Briefs, invitations, marketplace, applications | campaign | 2000 | ✅ Implemented |
| [e3-collaboration](e3-collaboration.md) | Deliverables, status pipeline, submissions | collaboration | 4000 | ✅ Implemented (file uploads are refs-only) |
| [e6-profiles-discovery](e6-profiles-discovery.md) | Socials, media kit, rate cards, brand directory | profile, discovery | 6060/9000 | 🟡 Base creator index done (Phase 1); rest is [Phase 3](../../../../docs/phases/phase-3-profile-discovery-depth.md) |
| [e4-endorsements](e4-endorsements.md) | Endorsement requests, two-way reviews | endorsement | 7000 | ⬜ [Phase 4](../../../../docs/phases/phase-4-endorsements-reviews.md) |
| [e8-payments](e8-payments.md) | Escrow, payouts, earnings | payments | 10000 | ⬜ [Phase 5](../../../../docs/phases/phase-5-payments-earnings.md) — new, not in the original epic list |
| [e5-notifications](e5-notifications.md) | Event bus, in-app + email | notification | 8000 | ⬜ [Phase 6](../../../../docs/phases/phase-6-notifications-outreach.md) |
| [e2-outreach](e2-outreach.md) | Templates, campaign-linked threads | messaging | 3000 | ⬜ [Phase 6](../../../../docs/phases/phase-6-notifications-outreach.md) |
| [e7-platform](e7-platform.md) | Media storage, verification, search, CI, **CORS** | cross-cutting | — | 🟡 CORS done; rest is [Phase 7](../../../../docs/phases/phase-7-platform-hardening-launch.md) |

> **Frontend specs** live in the `ndorsify-app` repo under the same path
> (`docs/plans/technical-specifications/`): `ui-foundation`, `p0-ui`, and
> `marketplace-ui` (current page inventory). The SPA requires **CORS on every
> service** — see [e7-platform §5](e7-platform.md).

## Shared conventions (all specs assume these)

- **Stack:** FastAPI · SQLAlchemy 2.0 async (`asyncpg`) · Pydantic v2 · Alembic ·
  one Postgres database per service. Tests: `pytest` on SQLite (`aiosqlite`).
- **Service shape:** `app/{routers,services,repositories,models,schemas,utils,core,db}`.
  A new service (`endorsement`, `payments`, `notification` — the three not
  yet built) needs: the layering above; `requirements.txt`, `Dockerfile`,
  `.env.example` (`PORT`, `DATABASE_URL`); an Alembic `0001_initial`
  migration; its own Postgres database registered in `docker-compose.yml`;
  `/health` + Swagger at `/api-docs.html`; `tests/` on `pytest` + SQLite
  (`aiosqlite`) with a `conftest.py` fixture.
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
