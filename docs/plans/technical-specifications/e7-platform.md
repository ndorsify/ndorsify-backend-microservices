# E7 · Platform & foundations (cross-cutting)

**Status:** 🟡 §5 CORS is done. Everything else is open — see
[phase-7-platform-hardening-launch](../../../../docs/phases/phase-7-platform-hardening-launch.md)
for current state, including launch-operational items (legal, observability,
deploy path) added there that this spec doesn't cover.

---

## 1. Media storage (unblocks E3 submissions, E6 media kit)

### Approach — direct-to-storage with signed URLs
Files never pass through the API. A small **`storage` module** (shared code,
copied per service, or a tiny `media-service`) issues signed upload/download URLs
against S3 (or Cloudinary / any S3-compatible store like R2/MinIO for local).

- `POST /media/sign-upload` → `{key, upload_url, fields}` — client PUTs the file
  directly to storage, then hands the returned `key` to E3/E6.
- `GET /media/sign-download?key=` → short-lived signed GET URL (private objects).
- Local dev: **MinIO** in docker-compose (S3-compatible), so no cloud account
  needed to develop.

### Data
No shared DB table — consuming services store the `key` (and content-type/size).
Keys are namespaced: `submissions/{collab_id}/…`, `media-kit/{user_id}/…`,
`avatars/{user_id}/…`.

### Env
`S3_ENDPOINT`, `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_REGION`.

### Security
Private by default; validate content-type + max size in the sign-upload request;
signed URLs expire in minutes; virus-scan is a P3 follow-up.

---

## 2. Email verification & roles/permissions  `users-service`

Builds on P0 auth. Verification endpoints and the `email_verified_at` gate are in
[p0-foundation](p0-foundation.md) §1. This item adds the **enforcement**:
- A `require_verified` dependency for actions that need a verified email
  (publishing a campaign, sending bulk outreach, receiving payouts later).
- The `require_role(...)` dependency applied consistently across all services'
  brand/creator/admin boundaries (audit that every mutating endpoint declares one).

---

## 3. Search  (Postgres full-text first)

Phase 1 deliberately avoids Algolia/Meilisearch.
- Each index table (`creator_index`, `brand_index`) has a `tsvector` column kept
  current with a trigger or on write, plus a **GIN index**.
- Query: `to_tsquery` for free text, combined with structured `WHERE` filters
  (niche/industry via JSONB `@>`, ranges on followers/budget).
- Ranking: `ts_rank` blended with a simple boost (rating, follower band).
- Revisit an external engine only if result quality or latency demands it; the
  discovery API contract stays the same, so it's a swappable backend.

---

## 4. Lint / format / CI (currently missing)

### Tooling (add to every service)
- **ruff** (lint + import sort) and **black** (format); config in a repo-root
  `pyproject.toml` shared by all services.
- **mypy** (optional, incremental) for the service/repository layers.

### CI — `.github/workflows/ci.yml`
Matrix over `microservices/*`:
1. set up Python 3.11, cache pip;
2. `pip install -r requirements.txt`;
3. `ruff check .` + `black --check .`;
4. `pytest -q` (SQLite, no DB needed).
Plus a job that runs `docker compose build` to catch Dockerfile drift.

### Pre-commit
`pre-commit` config running ruff + black on staged files (mirrors CI locally).

---

## 5. Frontend enablement — CORS & base URLs (required for the SPA)

The React client calls the services directly from the browser, so **every
service must send CORS headers** or all calls fail. This is a hard prerequisite
for any UI work (see the frontend `ui-foundation` spec in the `ndorsify-app`
repo).

- Add FastAPI **`CORSMiddleware`** to each service's `create_app()`, with
  **allowed origins from env** (`CORS_ORIGINS`, comma-separated) — never `*`
  once credentials/real origins are involved.
  ```python
  # app/main.py
  from fastapi.middleware.cors import CORSMiddleware
  app.add_middleware(
      CORSMiddleware,
      allow_origins=settings.cors_origins,   # e.g. ["http://localhost:3000"]
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
- Add `cors_origins: list[str]` to each `core/config.py` (default the local CRA
  origin `http://localhost:3000`).
- **Base-URL strategy:** until the API gateway lands, the SPA holds one base URL
  **per service** (five ports); the gateway later collapses these to one origin,
  which also simplifies CORS to a single allowed origin. This mirrors the
  frontend's `REACT_APP_*_URL` config.
- Because auth uses **Bearer tokens in a header** (not cookies), CSRF is not a
  concern; keep tokens out of cookies to preserve that.

## 6. Cross-cutting infra recap (for reference)
- **Postgres** — already in compose; add a database per new service.
- **Redis** — add to compose for: auth rate-limiting, notification dedupe/queue,
  and (later) real-time messaging fan-out.
- **Service-to-service token** — a shared secret in env used by internal
  endpoints (E1→E3 create, producers→E5 ingest); distinct from user JWTs.
- **CORS** — per service, origins from env (see §5).

## Tests
Sign-upload rejects oversize/bad content-type; signed URL expiry; `require_verified`
blocks unverified users; full-text query matches + ranks a fixture set; CI config
lints and tests green on a sample service.
