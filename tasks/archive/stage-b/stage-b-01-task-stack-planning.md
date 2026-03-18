# Task: stage-b-01-task-stack-planning

## Goal

Close Stage A formally, define Stage B as the next planning unit, and create the first Stage B task wave.

## Project Stage

- Stage: Stage B
- Track: shared planning across all three tracks

## Why

The repository should not leave Stage A half-open or move into new work without a fresh planning boundary. Stage B needs
its own planning document, naming rules, and execution-ready task stack.

## Context

Relevant documents:

- `STATUS.md`
- `DECISIONS.md`
- `docs/prd/STAGE_A_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `tasks/README.md`

## Flow Alignment

- Flow A / B / C / D: planning support for all flows
- Related APIs: none directly
- Related schema or storage changes: none

## Dependencies

- Prior task: `tasks/archive/stage-a/stage-a-09-staging-delivery-path.md`
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
  - formally close Stage A
  - define Stage B planning in text
  - define the first Stage B task wave
- Task changes:
  - create the first Stage B execution-ready task files
  - archive this planning task after completion

## Acceptance Criteria

- Stage A is explicitly closed in the planning docs
- Stage B is explicitly defined as the next planning unit
- the first Stage B task wave exists under `tasks/`

## Verification Commands

- Repository:
  - manual doc consistency review

## Tests

- Normal case:
  - a collaborator can identify the active stage and the next execution-ready task without consulting chat history
- Edge case:
  - archived Stage A material remains preserved and does not conflict with Stage B activation
- Error case:
  - the repository should not show both Stage A and Stage B as simultaneously active planning units

## Risks

- defining Stage B too vaguely could push ambiguity into the next execution wave

## Rollback Plan

- revert the Stage B planning docs and task files while keeping Stage A closed until a replacement planning unit is ready

## Results

- formally closed Stage A as complete
- created `docs/prd/STAGE_B_PLAN.md` for the next planning unit
- adopted `stage-b-*` naming for Stage B tasks
- created the first Stage B execution-ready task wave

## Execution Status

- Status: completed
- Completed At: 2026-03-18
- Notes: Stage B is now the active planning unit and Stage A remains preserved as a closed reference stage

## Verification Result

- manual doc consistency review
