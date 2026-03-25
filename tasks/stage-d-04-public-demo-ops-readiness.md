# Task: stage-d-04-public-demo-ops-readiness

## Goal

Create the bounded operator routine required to keep the public demo available, refreshable, and recoverable.

## Project Stage

- Stage: Stage D
- Track: Delivery and Operations with required Platform Reliability support

## Why

A public demo without a restart, refresh, rollback, and abuse-response routine quickly collapses back into an
unreliable local-only project. Stage D needs a bounded operator path instead of only a deployment aspiration.

## Context

Relevant documents:

- `docs/prd/STAGE_D_PLAN.md`
- `docs/development/DELIVERY_BASELINE.md`
- `docs/development/STAGING_RELEASE_PATH.md`
- `README.md`
- `STATUS.md`

## Flow Alignment

- Flow D: public-demo delivery, restart, rollback, and operator handoff
- Related APIs: health, auth, workspace access, demo-critical module paths
- Related schema or storage changes: none unless minimally required for demo refresh or operator visibility

## Dependencies

- Prior task: `tasks/stage-d-03-demo-content-seeding-and-showcase-path.md`
- Blockers:
  - `stage-d-02-public-demo-foundation-and-guardrails.md`
  - `stage-d-03-demo-content-seeding-and-showcase-path.md`

## Scope

Allowed files:

- `server/app/`
- `server/tests/`
- `web/`
- `scripts/`
- `docs/development/`
- `README.md`
- `STATUS.md`
- `DECISIONS.md`

Disallowed files:

- heavy production-operations automation
- unrelated module workflow expansion

## Deliverables

- Code or contract changes:
  - only the minimum operator-facing support needed for a stable public demo baseline
- Docs changes:
  - public-demo operator routine, restart path, rollback expectations, and refresh instructions

## Acceptance Criteria

- the operator can restart or refresh the demo without hidden tribal knowledge
- rollback expectations are explicit for the public demo baseline
- the public demo remains bounded and honest about its operational maturity

## Verification Commands

- Backend:
  - `cd server`
  - `..\\.venv\\Scripts\\python.exe -m pytest tests`
- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - a collaborator can follow the documented public-demo operator path
- Edge case:
  - stale demo content or failed refresh attempts are recoverable through the documented routine
- Error case:
  - the public-demo docs do not imply production-grade operations beyond what the repository actually supports

## Risks

- demo-ops work can easily overreach into a larger production-ops program if not kept bounded

## Rollback Plan

- revert the public-demo operator routine additions while preserving the earlier local and staging delivery baseline
