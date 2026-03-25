# Task: stage-d-01-task-stack-planning

## Goal

Close Stage C formally, define the long-term roadmap, define Stage D as the next bounded planning unit, and create the
first Stage D task wave.

## Project Stage

- Stage: Stage D
- Track: shared planning across all three tracks

## Why

Stage C completed its workflow-expansion and cross-module-readiness goals, but the project now needs two different
documents instead of one overloaded next-step plan:

- one long-range roadmap for learning-first direction across multiple future stages
- one bounded next stage focused only on the public internet demo baseline

## Context

Relevant documents:

- `STATUS.md`
- `CONTEXT.md`
- `DECISIONS.md`
- `docs/prd/PLATFORM_PRD.md`
- `docs/prd/STAGE_C_PLAN.md`
- `tasks/README.md`

## Flow Alignment

- Flow A / B / C / D: planning support for all flows
- Related APIs: none directly
- Related schema or storage changes: none

## Dependencies

- Prior task: `tasks/archive/stage-c/stage-c-14-cross-module-eval-coverage-and-rehearsal-evidence.md`
- Blockers: none

## Scope

Allowed files:

- `README.md`
- `CONTEXT.md`
- `STATUS.md`
- `DECISIONS.md`
- `docs/prd/`
- `docs/PROJECT_GUIDE.md`
- `tasks/`

Disallowed files:

- runtime feature code
- unrelated deployment changes

## Deliverables

- Docs changes:
  - formally close Stage C
  - create `docs/prd/LONG_TERM_ROADMAP.md`
  - create `docs/prd/STAGE_D_PLAN.md`
  - update the control plane and PRD docs to point at Stage D
- Task changes:
  - create the first Stage D execution-ready task files
  - archive this planning task after completion

## Acceptance Criteria

- Stage C is explicitly closed in the planning docs
- the long-term roadmap is separated from the next bounded stage
- Stage D is explicitly defined as the next planning unit
- the first Stage D execution-ready tasks exist under `tasks/`

## Verification Commands

- Repository:
  - manual doc consistency review

## Tests

- Normal case:
  - a collaborator can identify the active stage and the next execution-ready task without consulting chat history
- Edge case:
  - the long-term roadmap does not overload the bounded Stage D plan
- Error case:
  - the repository should not show both Stage C and Stage D as simultaneously active planning units

## Risks

- letting Stage D absorb the whole long-term roadmap would make it much broader than Stages A through C

## Rollback Plan

- revert the Stage D planning docs and task files while keeping Stage C closed until a replacement next-stage plan is ready

## Results

- formally closed Stage C as complete
- created `docs/prd/LONG_TERM_ROADMAP.md` for multi-stage direction
- created `docs/prd/STAGE_D_PLAN.md` for the next bounded stage
- adopted `stage-d-*` naming for Stage D tasks
- created the first Stage D execution-ready task wave

## Execution Status

- Status: completed
- Completed At: 2026-03-26
- Notes: Stage D is now the active planning unit and the long-term roadmap remains separate from the bounded next-stage scope

## Verification Result

- manual doc consistency review
