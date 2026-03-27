# Task: stage-d-08-public-internet-rollout-and-operator-rehearsal

## Goal

Execute and document the first bounded public internet rollout rehearsal for the demo environment.

## Project Stage

- Stage: Stage D
- Track: Delivery and Operations with required Platform Reliability support

## Why

The public-demo path is not truly finished until the repository has one real rollout rehearsal record: what was
launched, what URL was exercised, what smoke checks passed, and what rollback target applies.

## Context

Relevant documents:

- `docs/prd/STAGE_D_PLAN.md`
- `docs/development/PUBLIC_DEMO_OPERATOR_RUNBOOK.md`
- `docs/development/DELIVERY_BASELINE.md`
- the results of `stage-d-06` and `stage-d-07`
- `STATUS.md`

## Flow Alignment

- Flow D: real internet rollout, smoke validation, and operator evidence
- Related APIs: health, public-demo settings, public-demo templates, auth, workspace access
- Related schema or storage changes: none unless minimally required for rollout evidence or operator visibility

## Dependencies

- Prior task: `tasks/stage-d-07-public-demo-deployment-path-and-env-wiring.md`
- Blockers: chosen hosting target and repository-side deployment path must already exist

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
- rollout evidence or handoff artifacts referenced from docs when appropriate

Disallowed files:

- unrelated workflow expansion
- overclaiming production readiness

## Deliverables

- Code or contract changes:
  - only minimal changes required to complete the rollout rehearsal honestly
- Docs changes:
  - public rollout evidence, smoke result, rollback target, and operator follow-up notes

## Acceptance Criteria

- one bounded public internet rollout rehearsal is completed and recorded honestly
- the rehearsal captures the public URL, smoke checks, operator notes, and rollback expectations
- the repository remains clear about what is still demo-grade rather than production-grade

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python.exe -m pytest tests`
- Frontend:
  - `npm --prefix web run verify`
- Public demo scripts:
  - relevant public-demo smoke or refresh commands for the chosen target

## Tests

- Normal case:
  - the public URL and guided demo path are exercised and recorded
- Edge case:
  - any missing external prerequisite is captured explicitly instead of being silently skipped
- Error case:
  - the rollout record does not pretend that the demo is healthy if smoke checks or manual checks fail

## Risks

- trying to finish a real rollout without bounded evidence can collapse into vague claims instead of a reproducible deployment result

## Rollback Plan

- revert the rollout-specific changes while preserving the bounded deployment path and operator routine docs