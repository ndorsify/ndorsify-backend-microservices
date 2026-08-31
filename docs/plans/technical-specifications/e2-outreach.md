# E2 · Outreach upgrades  `messaging-service` (:3000)

**Status:** ⬜ Not started · See
[phase-6-notifications-outreach](../../../../docs/phases/phase-6-notifications-outreach.md).
**Depends on:** P0 base messaging (done — [p0-foundation](p0-foundation.md) §3).

Adds reusable outreach templates and campaign context to the existing 1:1 inbox.

---

## Data model (Alembic `0002_outreach`)

### `outreach_templates`
`id`, `brand_id` (user_id, indexed), `name`, `body` (with `{{merge_field}}`
placeholders), `created_at`, `updated_at`. Brand-owned.

### Extend `conversations`
Add `campaign_id` UUID nullable (indexed) — links a thread to a campaign so the
brief can be shown in context. Null = ordinary DM.

---

## API

### Templates
| Method | Path | Role | Notes |
|---|---|---|---|
| GET | `/templates` | brand | own templates |
| POST | `/templates` | brand | `{name, body}` |
| PUT | `/templates/{id}` | brand (owner) | |
| DELETE | `/templates/{id}` | brand (owner) | soft delete |
| POST | `/templates/{id}/render` | brand | `{context:{creator_name,...}}` → rendered body (server-side merge) |

### Campaign-linked threads
| Method | Path | Notes |
|---|---|---|
| POST | `/conversations` | now accepts optional `campaign_id` |
| GET | `/conversations?campaign_id=` | filter a brand's threads by campaign |

### Bulk outreach
| Method | Path | Role | Notes |
|---|---|---|---|
| POST | `/outreach/bulk` | brand | `{creator_ids[], template_id, context_overrides?}` → creates/finds a conversation per creator and posts the rendered message |

---

## Service logic
- **Merge rendering:** simple `{{field}}` substitution against a whitelist of
  fields (`creator_name`, `brand_name`, `campaign_title`). Unknown fields → left
  blank, never error. Escape output; templates are plain text in Phase 1.
- **Bulk send** is capped (e.g. ≤50 recipients/request) and rate-limited per brand
  to avoid spam; each send reuses the find-or-create conversation logic and emits
  `message.created`. Partial failures return a per-recipient result list.
- Campaign-linked threads let the frontend fetch the brief from campaign-service
  by `campaign_id` — messaging-service stores only the id.

## Frontend (`ndorsify-app`)
- Template manager (list/create/edit) in brand settings.
- "Message" action on a shortlist/marketplace card → pick template → preview
  rendered text → send (single or bulk).
- Thread view shows a campaign brief banner when `campaign_id` is set.

## Tests
Merge renders known fields and blanks unknowns; bulk send respects the cap and
returns per-recipient status; campaign filter returns only linked threads;
template ownership guard.
