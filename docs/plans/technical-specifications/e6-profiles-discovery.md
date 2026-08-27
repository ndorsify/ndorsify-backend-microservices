# E6 · Profile & discovery upgrades  `profile-service` (:6060) · `discovery-service` (:9000)

**Status:** Proposed · **Depends on:** P0 profiles & discovery base; E7 media
storage (media kit); E4 aggregate rating.

Turns bare profiles into campaign-ready ones and adds the brand directory.

---

## 1. Connected socials & audience stats  `profile-service`

### Data model
`social_accounts` — `id`, `user_id` (creator), `platform enum('instagram','youtube','tiktok','twitter')`,
`handle`, `external_id`, `access_token_enc` (encrypted at rest), `follower_count`,
`engagement_rate` numeric(5,2), `last_synced_at`, `created_at`.
Unique `(user_id, platform)`.

### API
| Method | Path | Notes |
|---|---|---|
| GET | `/social/{platform}/connect` | OAuth start for the platform's API |
| GET | `/social/{platform}/callback` | store tokens, initial stats fetch |
| POST | `/social/{platform}/sync` | refresh follower/engagement (rate-limited) |
| DELETE | `/social/{platform}` | disconnect |

### Logic
- Each platform has its own Graph/Data API (Instagram Graph, YouTube Data,
  TikTok). Wrap each behind a `SocialProvider` interface so services/tests can mock
  them; store only what we display (followers, engagement) plus the token.
- **Encrypt tokens at rest** (Fernet/`cryptography`, key from env). Never return
  tokens over the API.
- A periodic sync (daily) updates stats; on change, emit `profile.updated` so
  discovery reindexes (see below).

---

## 2. Media kit & rate card  `profile-service`

### Data model
- `media_kit_items` — `id`, `user_id`, `kind enum('image','video','link')`,
  `storage_key` (E7) or `url`, `caption`, `sort_order`.
- `rate_cards` — `id`, `user_id`, `platform`, `deliverable_type`, `price`
  numeric(12,2), `currency`. One row per offering.

### API
`GET/PUT /profiles/creators/me/media-kit` (bulk upsert of items),
`GET/PUT /profiles/creators/me/rate-card`, plus public
`GET /profiles/creators/{user_id}/media-kit`. Uploads use E7 signed URLs.

---

## 3. Progressive profile completion  `dynamic-content-service`

Extend onboarding: `completion_pct` (already on the profile) is computed from a
**checklist definition** served by dynamic-content-service so the required fields
are config, not code.
- `GET /onboard/{role}/checklist` → ordered required sections + weights.
- profile-service computes `completion_pct` against that checklist on write and
  exposes `GET /profiles/creators/me/completion` → `{pct, missing[]}` for nudges.

---

## 4. Brand directory  `discovery-service`

Mirror of the creator index for brands, so creators can browse brands + open
campaigns.

### Data model
`brand_index` — `user_id`, `company_name`, `industry`, `logo_url`, `open_campaigns`
int, `search_tsv` tsvector (GIN), `updated_at`. Populated from `profile.updated`
and campaign publish/close events.

### API
| Method | Path | Query |
|---|---|---|
| GET | `/discovery/brands` | `q, industry, has_open_campaigns, page, size, sort` |
| GET | `/discovery/creators` | *(from P0; now also filters `min_engagement`, sorts by rating)* |

The creator index gains `engagement_rate` and `avg_rating` columns (fed by
`profile.updated` and E4 `review.created`), enabling sort-by-rating.

## Frontend (`ndorsify-app`)
- Creator: connect-socials settings, media-kit editor, rate-card editor,
  completion meter with "finish your profile" nudges.
- Creator: brand directory browse view.

## Tests
Token encryption round-trip; provider interface mocked for stats sync;
completion math against a checklist fixture; brand directory filters;
creator sort-by-rating reflects E4 aggregates.
