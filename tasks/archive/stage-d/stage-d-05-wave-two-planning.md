# Task: stage-d-05-wave-two-planning

## Goal

Define the second executable Stage D task wave after the first Stage D wave completed the bounded public-demo baseline.

## Project Stage

- Stage: Stage D
- Track: Cross-track planning

## Why

The first Stage D wave made the system demo-safe and operator-readable, but the project still lacks the next bounded
step that turns that baseline into a real internet-accessible rollout instead of a well-prepared local or staging demo.

## Context

Relevant documents:

- `docs/prd/STAGE_D_PLAN.md`
- `docs/prd/LONG_TERM_ROADMAP.md`
- `docs/development/PUBLIC_DEMO_BASELINE.md`
- `docs/development/PUBLIC_DEMO_SHOWCASE_PATH.md`
- `docs/development/PUBLIC_DEMO_OPERATOR_RUNBOOK.md`
- `STATUS.md`
- `DECISIONS.md`
- `tasks/README.md`

Relevant completed tasks:

- `tasks/archive/stage-d/stage-d-02-public-demo-foundation-and-guardrails.md`
- `tasks/archive/stage-d/stage-d-03-demo-content-seeding-and-showcase-path.md`
- `tasks/archive/stage-d/stage-d-04-public-demo-ops-readiness.md`

## Flow Alignment

- Flow D: planning support for the public-demo rollout path
- Related APIs: none directly
- Related schema or storage changes: none directly

## Dependencies

- Prior task: `tasks/archive/stage-d/stage-d-04-public-demo-ops-readiness.md`
- Blockers: none

## Scope

Allowed files:

- `README.md`
- `CONTEXT.md`
- `STATUS.md`
- `DECISIONS.md`
- `docs/prd/`
- `docs/development/`
- `tasks/`

Disallowed files:

- runtime feature code
- unrelated workflow expansion
- real environment or secret changes

## Deliverables

- Docs changes:
  - define the second Stage D wave focused on real internet rollout
  - update planning and control-plane docs to point at the next active task
- Task changes:
  - create the second Stage D execution-ready task files
  - archive this planning task after completion

## Acceptance Criteria

- the second Stage D wave is fixed in text
- root `tasks/` contains the next execution-ready Stage D tasks
- `STATUS.md`, `DECISIONS.md`, and `docs/prd/STAGE_D_PLAN.md` all agree on the next Stage D wave

## Verification Commands

- Repository:
  - manual doc consistency review

## Tests

- Normal case:
  - a collaborator can identify the next Stage D task without consulting chat history
- Edge case:
  - the completed first Stage D wave remains archived and preserved while the second wave becomes active
- Error case:
  - no live control doc should still imply that Stage D is waiting on an undefined next step

## Risks

- defining the second Stage D wave too broadly could turn it into an unbounded deployment program instead of one bounded internet-rollout wave

## Rollback Plan

- revert the second-wave planning docs and task files while keeping the completed first Stage D wave intact

## Execution Status

- Status: completed
- Completed At: 2026-03-26
- Notes:
  - defined the second Stage D wave as `stage-d-06`, `stage-d-07`, and `stage-d-08`
  - updated the control-plane and PRD docs to point at the new wave
  - left the root `tasks/` directory ready for direct execution

## Result

- The second Stage D wave is now fixed as:
  - `tasks/stage-d-06-public-hosting-target-and-deployment-contract.md`
  - `tasks/stage-d-07-public-demo-deployment-path-and-env-wiring.md`
  - `tasks/stage-d-08-public-internet-rollout-and-operator-rehearsal.md`
- `stage-d-06` is the next active execution task.

## Verification Result

- manual consistency review across `STATUS.md`, `DECISIONS.md`, `CONTEXT.md`, `docs/prd/STAGE_D_PLAN.md`, and the new Stage D task specs