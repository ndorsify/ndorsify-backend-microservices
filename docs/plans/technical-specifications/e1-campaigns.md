# E1 · Campaigns  `campaign-service` (:2000, new)

**Status:** Proposed · **Depends on:** P0 auth/roles; profiles & discovery for the
full experience (invitations need shortlists, applications need creator profiles).

The spine of the marketplace: a brand publishes a brief, invites or receives
creators, and manages applications.

---

## Data model (Alembic `0001_initial`)

### `campaigns`
| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `brand_id` | UUID, indexed | user_id of the owning brand |
| `title` | str | |
| `objective` | text | |
| `deliverables` | JSONB | `[{platform, type, quantity}]` |
| `platforms` | JSONB | denormalized for filtering |
| `budget_amount` | numeric(12,2) | |
| `budget_currency` | str(3) | ISO 4217 |
| `starts_on` / `ends_on` | date | timeline |
| `target_audience` | JSONB | `{niches[], locations[], age_range}` |
| `status` | enum | `draft` → `open` → `closed` / `archived` |
| `published_at` | datetime nullable | set on publish |
| timestamps + `is_deleted` | | |

### `invitations`
`id`, `campaign_id`, `creator_id`, `status enum('pending','accepted','declined','withdrawn')`,
`message` text, `created_at`, `responded_at`. Unique `(campaign_id, creator_id)`.

### `applications`
`id`, `campaign_id`, `creator_id`, `proposal` text, `proposed_rate` numeric(12,2),
`status enum('submitted','accepted','rejected','withdrawn')`, `created_at`,
`decided_at`. Unique `(campaign_id, creator_id)`.

> A creator reaches a campaign via **either** an invitation **or** an application,
> never both — acceptance from either path is what feeds E3 (a Collaboration).

Indexes: `campaigns(status, published_at)` for the marketplace feed;
`invitations(creator_id, status)` and `applications(creator_id, status)` for a
creator's dashboards.

---

## API

### Campaign CRUD (brand)
| Method | Path | Role | Notes |
|---|---|---|---|
| POST | `/campaigns` | brand | create as `draft` |
| GET | `/campaigns/{id}` | any | brand sees own drafts; public sees only `open` |
| PATCH | `/campaigns/{id}` | brand (owner) | edit while `draft`/`open` |
| POST | `/campaigns/{id}/publish` | brand (owner) | `draft`→`open`, validates required fields, sets `published_at` |
| POST | `/campaigns/{id}/close` | brand (owner) | `open`→`closed` |
| GET | `/campaigns/mine` | brand | owner's campaigns, any status |

### Marketplace (creator)
| Method | Path | Query | Notes |
|---|---|---|---|
| GET | `/campaigns` | `q, platform, niche[], min_budget, max_budget, page, size, sort` | only `status=open`; paginated `Page` envelope |

### Invitations
| Method | Path | Role | Notes |
|---|---|---|---|
| POST | `/campaigns/{id}/invitations` | brand (owner) | `{creator_id, message}`; emits `campaign.invited` |
| GET | `/invitations/mine` | creator | creator's invitations |
| POST | `/invitations/{id}/respond` | creator (invitee) | `{decision: accepted\|declined}` → on accept, create Collaboration (E3) |

### Applications
| Method | Path | Role | Notes |
|---|---|---|---|
| POST | `/campaigns/{id}/applications` | creator | `{proposal, proposed_rate}`; only if `open`; emits `campaign.applied` |
| GET | `/campaigns/{id}/applications` | brand (owner) | review list |
| POST | `/applications/{id}/decide` | brand (owner) | `{decision: accepted\|rejected}`; on accept → create Collaboration (E3), emits `application.accepted`/`application.rejected` |

---

## Service logic

- **Publish validation:** title, objective, ≥1 deliverable, budget, and timeline
  must be present; reject otherwise (422 with field list).
- **State machine:** `draft→open→closed`; `archived` from any. Guard transitions in
  the service layer; illegal transition → 409.
- **Acceptance → Collaboration:** accepting an invitation or an application calls
  collaboration-service (`POST /collaborations`, HTTP via `httpx`) with
  `{campaign_id, creator_id, brand_id, deliverables}`. If that call fails, mark the
  acceptance `pending_link` and retry — do not leave an accepted-but-unlinked state
  silently. (Simplest Phase-1 version: synchronous call, surface the error.)
- **Discovery hook:** invitations are typically created from a discovery shortlist;
  campaign-service only stores the `creator_id`.

## Events emitted
`campaign.invited {invitation_id, campaign_id, creator_id, brand_id}` ·
`campaign.applied {application_id, campaign_id, creator_id, brand_id}` ·
`application.accepted` / `application.rejected` · `invitation.accepted` /
`invitation.declined`. All POSTed to notification-service (E5).

## Frontend (`ndorsify-app`)
- Brand: multi-step **brief builder** (objective → deliverables → budget/timeline →
  audience → review/publish); campaign list with status; applications review table.
- Creator: **marketplace** grid with filters; campaign detail + apply modal;
  "my invitations" and "my applications" views.

## Tests
Publish rejects incomplete brief (422); marketplace lists only `open`;
invite is unique per creator (409 on dup); application decide accepts→triggers
collaboration create (mock httpx); role guards on every brand/creator boundary.
