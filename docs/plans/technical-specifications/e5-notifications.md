# E5 · Notifications  `notification-service` (:8000, new)

**Status:** ⬜ Not started · See
[phase-6-notifications-outreach](../../../../docs/phases/phase-6-notifications-outreach.md).
**Consumes events from:** E1, E3, E4, and base messaging.

The single fan-out point: every meaningful state change becomes an in-app
notification and (optionally) an email.

---

## Event ingestion (no broker in Phase 1)

Producers **POST** events to a single ingest endpoint. This keeps Phase 1
broker-free; swapping to Redis Streams / a real broker later only changes the
transport behind this endpoint.

| Method | Path | Auth | Body |
|---|---|---|---|
| POST | `/events` | service token | `{type, actor_id, payload, occurred_at}` |

- Authenticated with the shared **service-to-service token** (not a user JWT).
- **Idempotency:** producers send an `event_id` (UUID); the endpoint dedupes on it
  (`processed_events` table) so retries are safe.
- The handler maps an event `type` → recipients + template (a static registry in
  `app/services/routing.py`), then writes notification rows and enqueues emails.

Known event types: `campaign.invited`, `campaign.applied`,
`application.accepted|rejected`, `invitation.accepted|declined`,
`deliverable.submitted|approved`, `changes.requested`, `collaboration.completed`,
`endorsement.requested|published`, `review.created`, `message.created`.

---

## Data model (Alembic `0001_initial`)
- `notifications` — `id`, `user_id` (indexed), `type`, `title`, `body`, `data` JSONB
  (deep-link ids), `read_at` nullable, `created_at`.
- `processed_events` — `event_id` PK, `processed_at` (idempotency ledger).
- `email_outbox` — `id`, `user_id`, `to_email`, `template`, `context` JSONB,
  `status enum('pending','sent','failed')`, `attempts`, `last_error`, `created_at`,
  `sent_at`. (Transactional outbox so email sending is retryable and decoupled.)
- `notification_prefs` — `user_id` PK, `channels` JSONB (`{email:bool, inapp:bool}`
  per category), `digest enum('off','daily','weekly')`. (Preferences UI is P3; the
  table exists now with sensible defaults.)

---

## API (user-facing)
| Method | Path | Notes |
|---|---|---|
| GET | `/notifications` | current user, paginated; `?unread=true` |
| GET | `/notifications/unread-count` | for the badge |
| POST | `/notifications/{id}/read` | mark one read |
| POST | `/notifications/read-all` | |

## Email delivery
- **Provider:** Postmark or SendGrid (SES if already on AWS) — see e7 for the env
  var + account.
- **Outbox worker:** a background task (FastAPI startup task or a separate
  `python -m app.worker`) polls `email_outbox` for `pending`, renders the template,
  sends via the provider, and marks `sent`/`failed` with backoff on `attempts`.
- Templates live in `app/templates/email/<type>.html` with a shared layout.

## Service logic
- Respect `notification_prefs`: always write the in-app row; only enqueue email if
  the user's prefs allow it for that category (default on for high-signal events:
  invites, applications, approvals, reviews; off for `message.created` beyond a
  first-of-thread nudge to avoid noise).
- Deep links: `data` carries the ids the frontend needs to route
  (e.g. `{campaign_id}` or `{collaboration_id}`).

## Frontend (`ndorsify-app`)
- Bell icon with unread count (polls `/unread-count`); dropdown feed; click →
  deep-link via `data`; mark-read on open.

## Tests
Idempotent ingest (same `event_id` twice → one notification); routing maps each
event type to the right recipients; prefs suppress email but keep in-app; outbox
worker marks sent/failed and retries; unread-count accuracy.
