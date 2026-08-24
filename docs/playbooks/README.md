# Playbooks

Operational runbooks and repeatable procedures — for humans and AI agents alike.

A playbook is a step-by-step guide for a recurring task: releasing, rotating a
secret, onboarding a service, responding to a specific alert, seeding data.

Suggested shape: When to use this · Prerequisites · Steps (numbered, copy-pasteable)
· Verification · Rollback / if it goes wrong.

Name files `verb-noun.md` (e.g. `release-frontend.md`, `rotate-api-keys.md`).
Keep steps concrete enough that an agent can execute them without guessing.
