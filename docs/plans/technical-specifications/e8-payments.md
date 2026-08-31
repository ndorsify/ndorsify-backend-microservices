# E8 · Payments, escrow & payouts  `payments-service` (:10000, new)

**Status:** Proposed · **Depends on:** E1 campaigns (funding a campaign),
E3 collaborations (release ties to deliverable approval); **New epic** — not
in the original Phase 1 plan, added because the frontend already has a
`CheckoutPage` and an `/earnings` console with no service behind either.

The launch blocker: a two-sided marketplace with no real money movement is a
demo, not a product. This service owns funding a campaign into escrow,
releasing it to a creator as deliverables are approved, and payouts.

---

## Approach — hold funds via a payment processor, don't move money ourselves

Use a processor with built-in marketplace/connected-account support (Stripe
Connect is the reference choice — destination charges + Stripe-held balances)
rather than custody funds directly. This service is a ledger and orchestrator
over the processor's API, not a bank.

- **Brand funds a campaign** → a charge (or a hold, depending on the
  processor's escrow primitive) against the brand's payment method, recorded
  as `escrow_amount` on the campaign.
- **Creator connects a payout account** (Stripe Connect Express onboarding)
  before they can receive a release.
- **Release** happens per-deliverable (or per-collaboration on `live`,
  configurable) once collaboration-service reports `approved`/`live` —
  transfers the deliverable's share from escrow to the creator's connected
  account.
- **Platform fee** taken as a percentage on release (the "service fee" line
  item the frontend `CheckoutPage`/`CampaignBuilderPage` already display as
  static numbers today).

## Data model (Alembic `0001_initial`)

### `escrow_accounts`
`id`, `campaign_id` (unique, indexed), `brand_id`, `currency`,
`funded_amount` numeric(12,2), `released_amount` numeric(12,2) default 0,
`status enum('unfunded','funded','partially_released','released','refunded')`,
`processor_ref` (charge/payment-intent id), timestamps.

### `payout_accounts`
`id`, `user_id` (creator, unique), `processor_account_id` (Connect account
id), `status enum('pending','enabled','restricted')`, `created_at`.

### `ledger_entries`
`id`, `escrow_account_id`, `type enum('fund','release','fee','refund')`,
`amount` numeric(12,2), `deliverable_id` nullable (which release this is
for), `processor_ref`, `created_at`. Append-only — the source of truth for
everything the Earnings screen displays; `escrow_accounts.released_amount` is
a denormalized rollup kept in sync in the same transaction as each insert.

### `payouts`
`id`, `user_id`, `amount`, `status enum('in_transit','paid','failed')`,
`processor_ref`, `created_at`, `paid_at`. One row per processor payout event
(a creator's connected account may batch multiple releases into one payout —
this table tracks the payout side, `ledger_entries` tracks the release side).

---

## API

| Method | Path | Role | Notes |
|---|---|---|---|
| POST | `/campaigns/{id}/fund` | brand (owner) | `{payment_method_id}` → creates the charge/hold, `escrow_accounts` row → `funded`; only callable once, only on a `published`/`open` campaign |
| GET | `/campaigns/{id}/escrow` | participant | funded/released amounts, status |
| POST | `/payout-accounts/connect` | creator | starts Connect Express onboarding, returns the processor's hosted onboarding URL |
| GET | `/payout-accounts/me` | creator | onboarding/enabled status |
| POST | `/internal/release` | service (collaboration-service) | `{collaboration_id, deliverable_id, amount}`; internal, service-token auth — called when a deliverable is approved/live |
| GET | `/earnings/me` | creator | paid YTD, in-escrow, available-for-payout, per-deal breakdown — backs the `/earnings` screen directly |
| GET | `/ledger/campaign/{id}` | participant | itemized ledger for a campaign (brand-side spend detail) |

## Service logic

- **Funding is synchronous with the processor call** — if the charge fails,
  the campaign stays unfunded and the brand sees the processor's decline
  reason, not a generic error (this is the fix for `CheckoutPage`'s currently
  hardcoded, unconnected "Fund & send invites" button).
- **Release is triggered by collaboration-service**, not polled — add a
  `POST /internal/release` call to collaboration-service's approve/mark-live
  handlers (`e3-collaboration` §API), authenticated with the shared
  service-to-service token, mirroring the existing campaign→collaboration
  pattern from Phase 1.
- **Idempotency**: releases carry the `deliverable_id` as a natural dedupe
  key — a retried release for an already-released deliverable is a no-op,
  not a double-pay.
- **Refunds**: closing a campaign with unreleased escrow triggers a refund of
  the unreleased balance back to the brand (manual trigger in Phase 5's first
  cut; automatic-on-close is a fast-follow).
- **Fees**: computed at fund-time as a percentage line (matches the
  "service fee" row the checkout UI already renders statically), held back
  from each release rather than charged separately.

## Events emitted
`escrow.funded`, `escrow.released {deliverable_id, amount}`,
`payout.paid`, `payout.failed` → notification-service
([Phase 6](../../../../docs/phases/phase-6-notifications-outreach.md)), once
that phase exists.

## Frontend (`ndorsify-app`)
- `CheckoutPage` (`src/features/checkout/`) wires to `POST /campaigns/{id}/fund`
  instead of its current hardcoded total (see the Phase 1 code-review finding
  on the hardcoded `total`).
- Creator: Connect onboarding CTA (redirect to the processor's hosted flow)
  gating "Open to work" / offer-acceptance until `payout_accounts` is
  `enabled`.
- `/earnings` console reads `GET /earnings/me` instead of `sampleData.js` —
  same tiles (paid YTD, in escrow, available, avg per deal), payouts table,
  now backed by `ledger_entries`/`payouts`.

## Tests
Fund is idempotent (second call on an already-funded campaign is rejected,
not double-charged); release is idempotent per `deliverable_id`; ledger sum
always equals `escrow_accounts.released_amount`; release blocked until the
creator's payout account is `enabled`; refund on close only refunds the
unreleased balance; internal release endpoint rejects a user JWT (requires
service token, same pattern as `e3-collaboration`'s internal create).
