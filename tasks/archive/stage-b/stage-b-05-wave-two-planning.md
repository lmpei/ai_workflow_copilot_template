# Task: stage-b-05-wave-two-planning

## Goal

Define the second executable Stage B task wave after the initial Research workbench, recoverable runtime controls, and
staging rehearsal baseline completed.

## Project Stage

- Stage: Stage B
- Track: Cross-track planning

## Why

The first Stage B wave established the first reusable Research workbench layer plus runtime and delivery baselines, but
it did not complete Stage B. The project now needs an ordered second wave so Stage B can continue productizing Research
without drifting into ad hoc follow-up work.

## Context

Relevant documents:

- `docs/prd/STAGE_B_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `STATUS.md`
- `DECISIONS.md`
- `tasks/README.md`

Relevant completed tasks:

- `tasks/archive/stage-b/stage-b-02-research-workbench-and-asset-lifecycle.md`
- `tasks/archive/stage-b/stage-b-03-recoverable-runtime-and-control-actions.md`
- `tasks/archive/stage-b/stage-b-04-staging-rehearsal-automation-and-handoff.md`

## Flow Alignment

- Flow A / B / C / D: planning alignment for Flow B / C / D
- Related APIs: none directly
- Related schema or storage changes: none directly

## Dependencies

- Prior task: `tasks/archive/stage-b/stage-b-04-staging-rehearsal-automation-and-handoff.md`
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
  - define the second Stage B wave
  - create execution-ready `stage-b-*` task specs
  - update control-plane and planning docs to point at the next active task

## Acceptance Criteria

- the second Stage B wave is fixed in text
- root `tasks/` contains the next execution-ready Stage B tasks
- `STATUS.md`, `DECISIONS.md`, and `docs/prd/STAGE_B_PLAN.md` all agree on the next Stage B wave

## Verification Commands

- Repository:
  - manual consistency review across planning docs and task references

## Tests

- Normal case:
  - a collaborator can tell which Stage B task is next without reading chat history
- Edge case:
  - historical Stage B task archives remain intact while the next wave is still discoverable
- Error case:
  - no live control doc should still imply that the first Stage B wave is the next work item

## Risks

- planning can become too vague if the second wave is not broken into execution-sized tasks

## Rollback Plan

- revert the second-wave planning docs and task specs while keeping the already completed Stage B work intact

## Execution Status

- Status: completed
- Completed At: 2026-03-18
- Notes:
  - defined the second Stage B wave as `stage-b-06`, `stage-b-07`, and `stage-b-08`
  - updated the control-plane and PRD docs to point at the new wave
  - left the root `tasks/` directory ready for direct execution

## Result

- The second Stage B wave is now fixed as:
  - `tasks/stage-b-06-research-briefs-and-asset-comparison.md`
  - `tasks/stage-b-07-runtime-recovery-history-and-operator-visibility.md`
  - `tasks/stage-b-08-release-evidence-and-rehearsal-records.md`
- `stage-b-06` is the next active execution task.

## Verification Result

- manual consistency review across `STATUS.md`, `DECISIONS.md`, `docs/prd/STAGE_B_PLAN.md`,
  `docs/prd/PLATFORM_PRD.md`, `README.md`, and the new Stage B task specs
