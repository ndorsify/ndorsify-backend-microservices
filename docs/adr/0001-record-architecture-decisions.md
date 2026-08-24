# 1. Record architecture decisions

Date: 2026-08-24

## Status

Accepted

## Context

We need to record the architectural decisions made on this project — why we
chose an approach, what we traded away, and what became true as a result. Kept
in the repo, these records give coding agents and new engineers the *reasoning*
behind the code, which the code itself cannot show.

## Decision

We will use Architecture Decision Records, as described by Michael Nygard.

- One file per decision under `docs/adr/`, numbered sequentially and never
  renumbered: `NNNN-title-in-kebab-case.md`.
- Each record has: Title, Date, Status, Context, Decision, Consequences.
- Status is one of: Proposed, Accepted, Deprecated, or Superseded by [NNNN].
- Records are immutable once Accepted. To change a decision, write a new ADR
  that supersedes the old one rather than editing history.

## Consequences

- The knowledge base carries decision history that survives team turnover.
- `AGENTS.md` links to the ADR index so LLM agents can find the "why".
- A small discipline cost per significant decision, paid back at every "why is
  this like this?" moment later.
