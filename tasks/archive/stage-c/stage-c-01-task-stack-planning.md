# Task: stage-c-01-task-stack-planning

## Goal

Close Stage B formally, define Stage C as the next planning unit, and create the first Stage C task wave.

## Project Stage

- Stage: Stage C
- Track: shared planning across all three tracks

## Why

Stage B succeeded in making Research reusable and the runtime/delivery layers more operator-ready, but the platform
still needs a new planning boundary to broaden real workflow depth beyond Research. Stage C needs its own planning
document, naming rules, and execution-ready task stack.

## Context

Relevant documents:

- `STATUS.md`
- `DECISIONS.md`
- `docs/prd/STAGE_B_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `tasks/README.md`

## Flow Alignment

- Flow A / B / C / D: planning support for all flows
- Related APIs: none directly
- Related schema or storage changes: none

## Dependencies

- Prior task: `tasks/archive/stage-b/stage-b-08-release-evidence-and-rehearsal-records.md`
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
  - formally close Stage B
  - define Stage C planning in text
  - define the first Stage C task wave
- Task changes:
  - create the first Stage C execution-ready task files
  - archive this planning task after completion

## Acceptance Criteria

- Stage B is explicitly closed in the planning docs
- Stage C is explicitly defined as the next planning unit
- the first Stage C task wave exists under `tasks/`

## Verification Commands

- Repository:
  - manual doc consistency review

## Tests

- Normal case:
  - a collaborator can identify the active stage and the next execution-ready task without consulting chat history
- Edge case:
  - archived Stage B material remains preserved and does not conflict with Stage C activation
- Error case:
  - the repository should not show both Stage B and Stage C as simultaneously active planning units

## Risks

- defining Stage C too vaguely could spread the next wave across too many modules without a clear shared standard

## Rollback Plan

- revert the Stage C planning docs and task files while keeping Stage B closed until a replacement planning unit is ready

## Results

- formally closed Stage B as complete
- created `docs/prd/STAGE_C_PLAN.md` for the next planning unit
- adopted `stage-c-*` naming for Stage C tasks
- created the first Stage C execution-ready task wave

## Execution Status

- Status: completed
- Completed At: 2026-03-21
- Notes: Stage C is now the active planning unit and Stage B remains preserved as a closed reference stage

## Verification Result

- manual doc consistency review