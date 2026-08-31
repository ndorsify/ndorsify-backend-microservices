# E4 · Endorsements & reviews  `endorsement-service` (:7000, new)

**Status:** ⬜ Not started · See
[phase-4-endorsements-reviews](../../../../docs/phases/phase-4-endorsements-reviews.md).
**Depends on:** E3 (done — reviews gate on a completed collaboration); E6
(aggregate rating surfaces on profiles, still open).

The product's namesake loop: a brand requests an endorsement, the creator
fulfills it, and both sides review each other once the work is live.

---

## Data model (Alembic `0001_initial`)

### `endorsement_requests`
| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `collaboration_id` | UUID, indexed | source of truth for eligibility |
| `brand_id` / `creator_id` | UUID | |
| `message` | text | brand's ask |
| `status` | enum `pending → fulfilled → published` / `declined` | |
| `content_ref` | JSONB nullable | the published endorsement (link/media key) |
| timestamps | | |

### `reviews`
`id`, `collaboration_id`, `author_id`, `author_role enum('brand','creator')`,
`subject_id`, `rating` smallint (1–5), `body` text, `created_at`.
Unique `(collaboration_id, author_id)` — one review per person per collaboration.

### `rating_aggregates` (materialized per subject)
`subject_id` PK, `count` int, `sum` int, `avg` numeric(3,2), `updated_at`.
Updated transactionally whenever a review is written.

---

## API
| Method | Path | Role | Notes |
|---|---|---|---|
| POST | `/endorsements/requests` | brand | `{collaboration_id, message}`; only if collaboration reached `live`; emits `endorsement.requested` |
| GET | `/endorsements/requests/mine` | creator/brand | own side |
| POST | `/endorsements/requests/{id}/fulfill` | creator | `{content_ref}` → `fulfilled` |
| POST | `/endorsements/requests/{id}/publish` | creator | `fulfilled`→`published`; emits `endorsement.published` |
| POST | `/reviews` | brand/creator | `{collaboration_id, rating, body}`; see eligibility |
| GET | `/reviews/subject/{user_id}` | any | paginated, public |
| GET | `/ratings/{user_id}` | any | `{count, avg}` from `rating_aggregates` |

## Service logic
- **Eligibility:** `POST /reviews` and `POST /endorsements/requests` verify the
  collaboration is `live`/`completed` by calling collaboration-service
  (`GET /collaborations/{id}`, `httpx`) and that the author is a participant.
  Reject otherwise (409).
- **One review per author per collaboration** (unique constraint → 409 on repeat).
- **Aggregate update:** writing a review updates `rating_aggregates` for the
  subject in the same transaction (`count+1`, `sum+rating`, recompute `avg`). This
  is the number E6 reads for profile display; expose it via `GET /ratings/{id}` so
  profile-service can pull or cache it.
- Endorsement `content_ref` may be a storage key (E7) or an external URL to the
  live post.

## Events emitted
`endorsement.requested` · `endorsement.published` · `review.created {subject_id, rating}`.
→ notification-service (E5).

## Frontend (`ndorsify-app`)
- Brand: "request endorsement" from a completed collaboration.
- Creator: fulfill/publish flow.
- Both: review form (rating stars + text), shown only when eligible; rating +
  reviews rendered on the public profile (E6).

## Tests
Review blocked before collaboration is live (409); duplicate review blocked;
aggregate math after N reviews; endorsement status machine
(`pending→fulfilled→published`); eligibility check mocks collaboration-service.
