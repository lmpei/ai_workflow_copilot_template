# Task: stage-c-11-wave-two-planning

## Goal

Define the second executable Stage C task wave after the first Stage C wave completed Support depth, Job depth, and the
lightweight cross-module readiness baseline.

## Project Stage

- Stage: Stage C
- Track: Cross-track planning

## Why

The first Stage C wave proved that Support and Job can move beyond runnable skeletons, but the repository still needs a
bounded next wave so those modules can deepen into multi-step workflows without drifting into ad hoc follow-up work.

## Context

Relevant documents:

- `docs/prd/STAGE_C_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `STATUS.md`
- `DECISIONS.md`
- `tasks/README.md`

Relevant completed tasks:

- `tasks/archive/stage-c/stage-c-02-support-copilot-grounded-case-workflow.md`
- `tasks/archive/stage-c/stage-c-03-job-assistant-structured-hiring-workflow.md`
- `tasks/archive/stage-c/stage-c-04-cross-module-quality-and-demo-readiness.md`

## Flow Alignment

- Flow A / B / C / D: planning support for all scenario-module flows
- Related APIs: none directly
- Related schema or storage changes: none directly

## Dependencies

- Prior task: `tasks/archive/stage-c/stage-c-04-cross-module-quality-and-demo-readiness.md`
- Blockers: none

## Scope

Allowed files:

- `README.md`
- `CONTEXT.md`
- `STATUS.md`
- `DECISIONS.md`
- `docs/prd/`
- `tasks/`

Disallowed files:

- runtime feature code
- unrelated deployment changes

## Deliverables

- Docs changes:
  - define the second Stage C wave
  - update planning and control-plane docs to point at the next active task
- Task changes:
  - create the second Stage C execution-ready task files
  - archive this planning task after completion

## Acceptance Criteria

- the second Stage C wave is fixed in text
- root `tasks/` contains the next execution-ready Stage C tasks
- `STATUS.md`, `DECISIONS.md`, and `docs/prd/STAGE_C_PLAN.md` all agree on the next Stage C wave

## Verification Commands

- Repository:
  - manual doc consistency review

## Tests

- Normal case:
  - a collaborator can identify the next Stage C task without consulting chat history
- Edge case:
  - the first Stage C wave remains archived and preserved while the second wave is active
- Error case:
  - no live control doc should still imply that the first Stage C wave is the next work item

## Risks

- defining the second Stage C wave too vaguely could spread the next work across multiple modules without a shared theme

## Rollback Plan

- revert the second-wave planning docs and task files while keeping the completed first Stage C wave intact

## Execution Status

- Status: completed
- Completed At: 2026-03-25
- Notes:
  - defined the second Stage C wave as `stage-c-12`, `stage-c-13`, and `stage-c-14`
  - updated the control-plane and PRD docs to point at the new wave
  - left the root `tasks/` directory ready for direct execution

## Result

- The second Stage C wave is now fixed as:
  - `tasks/stage-c-12-support-escalation-and-follow-up-workflow.md`
  - `tasks/stage-c-13-job-shortlist-and-candidate-comparison.md`
  - `tasks/stage-c-14-cross-module-eval-coverage-and-rehearsal-evidence.md`
- `stage-c-12` is the next active execution task.

## Verification Result

- manual consistency review across `STATUS.md`, `DECISIONS.md`, `CONTEXT.md`, `README.md`, `docs/prd/STAGE_C_PLAN.md`,
  `docs/prd/PLATFORM_PRD.md`, and the new Stage C task specs
