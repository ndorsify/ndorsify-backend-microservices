# E3 · Collaboration tracking  `collaboration-service` (:4000, new)

**Status:** Proposed · **Depends on:** E1 (campaigns create collaborations on
acceptance); E7 media storage (for submission files).

Tracks an accepted brand↔creator engagement from kickoff to live content.

---

## Data model (Alembic `0001_initial`)

### `collaborations`
| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `campaign_id` | UUID, indexed | from E1 |
| `brand_id` / `creator_id` | UUID, indexed | |
| `status` | enum | see state machine |
| `created_at` / `updated_at` | | |

### `deliverables`
`id`, `collaboration_id`, `platform`, `type`, `description`, `due_on` date,
`status enum('todo','submitted','changes_requested','approved','live')`,
`created_at`. Seeded from the campaign's `deliverables` at creation.

### `submissions`
`id`, `deliverable_id`, `version` int, `file_refs` JSONB (storage keys from E7),
`note` text, `submitted_by` (creator_id), `created_at`. Monotonic `version` per
deliverable.

### `reviews` (submission review actions)
`id`, `submission_id`, `decision enum('approved','changes_requested')`,
`feedback` text, `reviewed_by` (brand_id), `created_at`.

---

## State machine

**Collaboration:** `invited → accepted → in_progress → submitted → approved → live`
(+ `cancelled` from any non-terminal state). Derived/rolled up from deliverable
statuses:
- moves to `in_progress` when work starts;
- `submitted` when all deliverables are at least `submitted`;
- `approved` when all `approved`;
- `live` when all `live` (creator marks live after posting).

**Deliverable:** `todo → submitted → (approved | changes_requested)`;
`changes_requested → submitted` (new version); `approved → live`.

Transitions are enforced in the service layer (illegal → 409). A small pure
function `next_collab_status(deliverables)` computes the rollup and is unit-tested
in isolation.

---

## API
| Method | Path | Role | Notes |
|---|---|---|---|
| POST | `/collaborations` | service (E1) | `{campaign_id, brand_id, creator_id, deliverables[]}`; internal, auth via service token |
| GET | `/collaborations/mine` | brand/creator | filtered by role → own side |
| GET | `/collaborations/{id}` | participant | full detail + deliverables |
| POST | `/deliverables/{id}/submit` | creator | `{file_refs, note}` → new submission version; deliverable→`submitted`; emits `deliverable.submitted` |
| POST | `/deliverables/{id}/review` | brand | `{decision, feedback}` → `approved`\|`changes_requested`; emits event |
| POST | `/deliverables/{id}/mark-live` | creator | `approved`→`live` |
| GET | `/collaborations/{id}/timeline` | participant | merged submissions + reviews, chronological |

Internal `POST /collaborations` is authenticated with a **service-to-service
token** (shared secret in env), not a user JWT, since E1 calls it on the brand's
behalf.

## Events emitted
`deliverable.submitted {deliverable_id, collaboration_id, brand_id}` ·
`deliverable.approved {…, creator_id}` · `changes.requested {…, creator_id, feedback}` ·
`collaboration.completed` (on all-live). → notification-service (E5).

## Media (E7 dependency)
Submissions store **storage keys**, not blobs. The frontend uploads directly to
storage via a signed URL obtained from E7, then posts the returned key(s) here.

## Frontend (`ndorsify-app`)
- Brand: **collaboration board** grouped by status; deliverable review drawer
  (approve / request changes with feedback).
- Creator: **"my work"** list; submit-deliverable form (file upload + note);
  version history per deliverable.

## Tests
`next_collab_status` rollup for each combination; submit increments version;
`changes_requested` allows re-submit but `approved` does not; only the brand
participant can review, only the creator can submit/mark-live; internal create
rejects a user JWT (requires service token).
