# Task: stage-b-08-release-evidence-and-rehearsal-records

## Goal

Strengthen the Stage B staging routine by making release evidence and rehearsal records more explicit and reusable.

## Project Stage

- Stage: Stage B
- Track: Delivery and Operations

## Why

Stage B wave one made the staging rehearsal more repeatable, but the resulting evidence is still lightweight and easy
to lose. The next delivery wave should record what was verified, what changed, and what rollback target applies with
less hidden operator knowledge.

## Context

Relevant documents:

- `docs/prd/STAGE_B_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `docs/development/DELIVERY_BASELINE.md`
- `docs/development/STAGING_RELEASE_PATH.md`
- `README.md`

Relevant operational areas:

- `scripts/`
- `docs/development/`
- root control-plane docs

## Flow Alignment

- Flow A / B / C / D: supports all flows operationally
- Related APIs: none directly
- Related schema or storage changes: none unless release evidence is persisted intentionally

## Dependencies

- Prior task: `tasks/archive/stage-b/stage-b-05-wave-two-planning.md`
- Blockers: none

## Scope

Allowed files:

- `README.md`
- `CONTEXT.md`
- `STATUS.md`
- `docs/development/`
- `docs/PROJECT_GUIDE.md`
- `scripts/`

Disallowed files:

- unrelated runtime feature work
- heavy production-operations automation outside the current Stage B scope

## Deliverables

- Code changes:
  - add only the minimum helper automation needed to capture or standardize release evidence
- Docs changes:
  - make rehearsal records and handoff expectations easier to reuse
  - define what evidence a collaborator should preserve after a Stage B staging rehearsal

## Acceptance Criteria

- a collaborator can point to a concrete record of what was changed and verified during a Stage B rehearsal
- release evidence remains lightweight but more durable than ad hoc terminal output
- the resulting routine still does not imply unsupported production guarantees

## Verification Commands

- Repository:
  - manual doc consistency review
  - any affected helper scripts should run without obvious command-shape errors

## Tests

- Normal case:
  - a collaborator can complete a rehearsal and leave behind a reusable evidence record
- Edge case:
  - local-only smoke output does not get confused with release-like evidence
- Error case:
  - the evidence path does not overstate the current delivery maturity of the project

## Risks

- trying to formalize release evidence too much could turn a lightweight staging routine into premature process overhead

## Rollback Plan

- revert the release-evidence additions while preserving the Stage B rehearsal and handoff baseline
