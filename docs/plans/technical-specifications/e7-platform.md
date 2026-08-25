# E7 · Platform & foundations (cross-cutting)

**Status:** Proposed · Infrastructure and tooling several epics depend on.

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

## 5. Cross-cutting infra recap (for reference)
- **Postgres** — already in compose; add a database per new service.
- **Redis** — add to compose for: auth rate-limiting, notification dedupe/queue,
  and (later) real-time messaging fan-out.
- **Service-to-service token** — a shared secret in env used by internal
  endpoints (E1→E3 create, producers→E5 ingest); distinct from user JWTs.

## Tests
Sign-upload rejects oversize/bad content-type; signed URL expiry; `require_verified`
blocks unverified users; full-text query matches + ranks a fixture set; CI config
lints and tests green on a sample service.
