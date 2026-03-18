# Task: stage-b-04-staging-rehearsal-automation-and-handoff

## Goal

Turn the Stage A staging path into a more repeatable operator routine with stronger rehearsal automation and handoff discipline.

## Project Stage

- Stage: Stage B
- Track: Delivery and Operations

## Why

Stage A established a concrete staging path, but it is still intentionally lightweight and manual. Stage B should make
that path easier to repeat, easier to hand off, and easier to audit without pretending the project is already running a
full production-operations stack.

## Context

Relevant documents:

- `docs/prd/STAGE_B_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `docs/development/DELIVERY_BASELINE.md`
- `docs/development/STAGING_RELEASE_PATH.md`
- `docs/development/WINDOWS_SETUP.md`
- `README.md`

Relevant operational areas:

- `.env.example`
- `docker-compose.yml`
- `scripts/`
- `docs/development/`
- root control-plane docs

## Flow Alignment

- Flow A / B / C / D: supports all flows operationally
- Related APIs: none directly
- Related schema or storage changes: release and handoff process only if documented or minimally automated

## Dependencies

- Prior task: `tasks/archive/stage-b/stage-b-01-task-stack-planning.md`
- Blockers: none

## Scope

Allowed files:

- `README.md`
- `CONTEXT.md`
- `STATUS.md`
- `docs/development/`
- `docs/PROJECT_GUIDE.md`
- `scripts/`
- `.env.example`
- `docker-compose.yml`

Disallowed files:

- unrelated application runtime features
- production-only infrastructure outside the Stage B scope

## Deliverables

- Code changes:
  - add only the minimum helper or script orchestration needed to make staging rehearsal more repeatable
- Docs changes:
  - define clearer operator handoff expectations
  - capture what a release rehearsal should record, confirm, and hand off
  - keep the Stage B delivery path concrete without overstating production guarantees

## Acceptance Criteria

- a collaborator can rehearse a Stage B staging release with less hidden knowledge than Stage A
- release helpers and docs make it clear what was checked, what changed, and what the rollback target is
- the resulting routine is still lightweight enough for the current project scope

## Verification Commands

- Repository:
  - manual doc consistency review
  - any affected helper scripts should run without obvious command-shape errors

## Tests

- Normal case:
  - a collaborator can follow the docs and helpers to perform a repeatable staging rehearsal and record the result
- Edge case:
  - local shortcuts remain clearly separated from release-like behavior
- Error case:
  - the Stage B handoff path does not imply unsupported production guarantees

## Risks

- pushing too hard on automation could create accidental production assumptions or unnecessary operational complexity

## Rollback Plan

- revert the Stage B delivery automation changes while preserving the Stage A staging path baseline
