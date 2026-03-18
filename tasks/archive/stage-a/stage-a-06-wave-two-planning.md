# Task: stage-a-06-wave-two-planning

## Goal

Define the second executable Stage A task wave after the initial Research / Reliability / Delivery baseline completed.

## Project Stage

- Stage: Stage A
- Track: Cross-track planning

## Why

The first Stage A wave established the contract, report, trust, and delivery baselines. The project now needs the next
ordered task stack so Stage A can keep deepening Research instead of drifting into ad hoc follow-up work.

## Context

Relevant documents:

- `docs/prd/STAGE_A_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `STATUS.md`
- `DECISIONS.md`
- `tasks/README.md`

Relevant completed tasks:

- `tasks/archive/stage-a/stage-a-02-research-contracts-and-structured-results.md`
- `tasks/archive/stage-a/stage-a-03-research-report-assembly-and-surface.md`
- `tasks/archive/stage-a/stage-a-04-research-trust-and-regression-baseline.md`
- `tasks/archive/stage-a/stage-a-05-delivery-and-operations-baseline.md`

## Flow Alignment

- Flow A / B / C / D: planning alignment for Flow B / C / D
- Related APIs: none directly
- Related schema or storage changes: none directly

## Dependencies

- Prior task: `tasks/archive/stage-a/stage-a-05-delivery-and-operations-baseline.md`
- Blockers: none

## Scope

Allowed files:

- `STATUS.md`
- `DECISIONS.md`
- `CONTEXT.md`
- `README.md`
- `docs/prd/`
- `tasks/`

Disallowed files:

- runtime feature code
- deployment infrastructure beyond planning/docs references

## Deliverables

- Code changes:
  - none required
- Test changes:
  - none required
- Docs changes:
  - define the second Stage A wave
  - create execution-ready `stage-a-*` task specs
  - update control-plane and planning docs to point at the next active task

## Acceptance Criteria

- the second Stage A wave is fixed in text
- root `tasks/` contains the next execution-ready Stage A tasks
- `STATUS.md`, `DECISIONS.md`, and `docs/prd/STAGE_A_PLAN.md` all agree on the next Stage A wave

## Verification Commands

- Repository:
  - manual consistency review across planning docs and task references

## Tests

- Normal case:
  - a collaborator can tell which Stage A task is next without reading chat history
- Edge case:
  - historical Stage A and Phase 5 task archives remain intact while new work is still discoverable
- Error case:
  - no live control doc should still imply that the first Stage A wave is the next work item

## Risks

- planning can become too vague if the second wave is not broken into execution-sized tasks

## Rollback Plan

- revert the second-wave planning docs and task specs while keeping the already completed Stage A work intact

## Execution Status

- Status: completed
- Completed At: 2026-03-18
- Notes:
  - defined the second Stage A wave as `stage-a-07`, `stage-a-08`, and `stage-a-09`
  - updated the control-plane and PRD docs to point at the new wave
  - left the root `tasks/` directory ready for direct execution

## Result

- The second Stage A wave is now fixed as:
  - `tasks/stage-a-07-research-iteration-workflow.md`
  - `tasks/stage-a-08-research-eval-baseline.md`
  - `tasks/stage-a-09-staging-delivery-path.md`
- `stage-a-07` is the next active execution task.

## Verification Result

- manual consistency review across `STATUS.md`, `DECISIONS.md`, `docs/prd/STAGE_A_PLAN.md`,
  `docs/prd/PLATFORM_PRD.md`, `README.md`, and the new Stage A task specs
