# P0 · Foundation

**Status:** Proposed · **Blocks:** all of Phase 1

Covers the todo's "Phase 0 prerequisites": authentication, roles, profiles, and
the base messaging & discovery services that Phase 1 epics extend.

---

## 1. Authentication & roles  `users-service` (:1000)

### Data model (extend `users` table)
Add to the existing `Users` model (new Alembic migration `0002_auth`):

| Column | Type | Notes |
|---|---|---|
| `email` | `str` unique, indexed | login identity |
| `password_hash` | `str` nullable | null for OAuth-only accounts |
| `role` | `enum('brand','creator','admin')` | drives access control |
| `email_verified_at` | `datetime` nullable | gates sensitive actions |
| `status` | `enum('active','suspended')` | default `active` |

New tables:
- `oauth_accounts` — `id`, `user_id`, `provider('google'|'facebook'|'twitter')`, `provider_user_id`, `created_at`; unique `(provider, provider_user_id)`.
- `refresh_tokens` — `id`, `user_id`, `token_hash`, `expires_at`, `revoked_at`.
- `password_reset_tokens` — `id`, `user_id`, `token_hash`, `expires_at`, `used_at`.

### Dependencies
`passlib[bcrypt]` (hashing), `pyjwt` (tokens), `authlib` or `httpx` (OAuth code exchange).

### API
| Method | Path | Body → Response | Notes |
|---|---|---|---|
| POST | `/auth/register` | `{email,password,role}` → `{user, tokens}` | creates user; sends verify email |
| POST | `/auth/login` | `{email,password}` → `{access,refresh}` | 401 on bad creds |
| POST | `/auth/refresh` | `{refresh}` → `{access,refresh}` | rotates refresh token |
| POST | `/auth/logout` | `{refresh}` → 204 | revokes refresh token |
| POST | `/auth/verify-email` | `{token}` → 204 | sets `email_verified_at` |
| POST | `/auth/forgot-password` | `{email}` → 204 | always 204 (no user enumeration) |
| POST | `/auth/reset-password` | `{token,password}` → 204 | |
| GET | `/auth/oauth/{provider}/start` | → redirect | PKCE where supported |
| GET | `/auth/oauth/{provider}/callback` | `?code` → `{tokens}` | links/creates via `oauth_accounts` |
| GET | `/auth/me` | → current user | requires Bearer |

### Tokens & shared dependency
- **Access JWT** (~15 min): claims `sub=user_id`, `role`, `exp`. HS256 with
  `JWT_SECRET` (per-env), or RS256 if we want services to verify without the secret.
- **Refresh** (~30 days): opaque, hashed at rest in `refresh_tokens`, rotated on use.
- Ship a small `require_auth` / `require_role(...)` FastAPI dependency. **It must be
  copyable into every service** (no shared package in Phase 1) — it only needs the
  public key / shared secret to verify, not DB access.

### Logic notes
- Register hashes with bcrypt; OAuth callback finds-or-creates the user and links
  an `oauth_accounts` row; email collision on OAuth links to the existing user only
  if that email is already verified, else requires confirmation.
- Rate-limit `/auth/login` and `/auth/forgot-password` (see e7 — reuse Redis).

### Tests
Register→login→refresh→logout happy path; wrong password 401; reset-token single-use;
OAuth callback find-or-create; `require_role` rejects mismatched role (403).

---

## 2. Profiles  `profile-service` (:6060)

Flesh out the skeleton. Two profile shapes keyed by `user_id`.

### Data model
- `creator_profiles` — `id`, `user_id` (unique), `display_name`, `bio`, `niches` (JSONB array), `location`, `languages` (JSONB), `avatar_url`, `completion_pct` (int), timestamps.
- `brand_profiles` — `id`, `user_id` (unique), `company_name`, `industry`, `logo_url`, `website`, `about`, timestamps.

(Social accounts, media kit, rate card, aggregate rating are added in
[e6-profiles-discovery](e6-profiles-discovery.md).)

### API
| Method | Path | Notes |
|---|---|---|
| GET | `/profiles/creators/{user_id}` | public creator profile |
| PUT | `/profiles/creators/me` | upsert own creator profile (role=creator) |
| GET | `/profiles/brands/{user_id}` | public brand profile |
| PUT | `/profiles/brands/me` | upsert own brand profile (role=brand) |
| GET | `/health` | |

`completion_pct` is recomputed on every write from required-field presence.

### Tests
Upsert creates then updates; role guard (creator cannot write a brand profile);
completion percentage math.

---

## 3. Base direct messaging  `messaging-service` (:3000, new)

Minimal 1:1 inbox; [e2-outreach](e2-outreach.md) adds templates & campaign links.

### Data model
- `conversations` — `id`, `participant_a` (user_id), `participant_b`, `last_message_at`; unique on the ordered participant pair.
- `messages` — `id`, `conversation_id`, `sender_id`, `body`, `read_at` nullable, `created_at`.

### API
| Method | Path | Notes |
|---|---|---|
| GET | `/conversations` | current user's threads, paginated, newest first |
| POST | `/conversations` | `{recipient_id}` → find-or-create |
| GET | `/conversations/{id}/messages` | paginated |
| POST | `/conversations/{id}/messages` | `{body}`; emits `message.created` |
| POST | `/conversations/{id}/read` | marks messages read |

Real-time delivery is out of scope for P0 (poll on an interval); WebSocket/SSE
is a fast-follow. Emits `message.created` to notification-service.

### Tests
Find-or-create idempotency; only participants can read/post (403 otherwise);
unread → read transition.

---

## 4. Base creator discovery  `discovery-service` (:9000, new)

Search over creator profiles. [e6](e6-profiles-discovery.md) adds the brand
directory and richer filters.

### Approach
Phase 1 uses **Postgres full-text + filtered queries** — no external search engine.
Two options for data:
- **(a) Query profile-service's DB read-replica** — simplest, but couples DBs.
- **(b) Maintain a local `creator_index` table** populated from `profile.updated`
  events. **Recommended** — keeps services decoupled and lets us add ranking.

### Data model (option b)
`creator_index` — `user_id`, `display_name`, `niches` (JSONB, GIN-indexed),
`location`, `follower_count`, `engagement_rate`, `search_tsv` (tsvector, GIN),
`updated_at`.

### API
| Method | Path | Query params | Notes |
|---|---|---|---|
| GET | `/discovery/creators` | `q, niche[], min_followers, max_followers, platform, location, page, size, sort` | ranked results |
| GET | `/discovery/shortlists` | | brand's shortlists |
| POST | `/discovery/shortlists` | `{name}` | brand's saved list |
| POST | `/discovery/shortlists/{id}/items` | `{creator_id}` | add to shortlist |
| GET | `/discovery/shortlists/{id}` | | list contents |

`shortlists` / `shortlist_items` tables live here (brand-owned).

### Tests
Filter by niche + follower range; full-text match on display_name/bio;
shortlist add is idempotent per creator.

---

## Build order within P0
1. Auth + roles (unblocks the shared `require_auth` dependency everyone needs).
2. Profiles (needed by discovery + campaign invitations).
3. Messaging base · Discovery base (parallel).
