# Task: stage-a-04-research-trust-and-regression-baseline

## Goal

Establish the minimum trust baseline for Stage A Research by improving failure visibility, trace completeness, and
regression evaluation coverage.

## Project Stage

- Stage: Stage A
- Track: Platform Reliability

## Why

Research depth without trust will make the platform harder to evolve. Stage A needs a minimum reliability layer that
can detect regressions and explain failures while Research gets more capable.

## Context

Relevant documents:

- `docs/prd/STAGE_A_PLAN.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`

Relevant runtime areas:

- `server/app/services/`
- `server/app/repositories/`
- `server/app/schemas/`
- `server/tests/`

## Flow Alignment

- Flow A / B / C / D: Flow B / C / D
- Related APIs: tasks, evals, traces, analytics
- Related schema or storage changes: trace/eval metadata and failure categorization only if required

## Dependencies

- Prior task:
  - `tasks/archive/stage-a/stage-a-02-research-contracts-and-structured-results.md`
  - `tasks/stage-a-03-research-report-assembly-and-surface.md`
- Blockers: none

## Scope

Allowed files:

- `server/app/services/`
- `server/app/repositories/`
- `server/app/schemas/`
- `server/tests/`
- `docs/PROJECT_GUIDE.md`

Disallowed files:

- frontend-only polish work
- deployment files

## Deliverables

- Code changes:
  - clarify failure classes or failure reporting on key Research paths
  - strengthen trace completeness for Research task/report flows
  - add a minimum regression evaluation baseline for Stage A Research
- Test changes:
  - add or update regression-oriented tests and Research trust checks
- Docs changes:
  - document any durable reliability conventions that developers must follow

## Acceptance Criteria

- Research regressions become easier to detect
- failures on major Research paths become easier to diagnose
- traces carry enough information to review Research quality and failure reasons
- Stage A Research evolution has a minimum regression baseline

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python.exe -m pytest tests`

## Tests

- Normal case:
  - a healthy Research path records the expected trust and trace signals
- Edge case:
  - weak or partial evidence produces explicit trust-related metadata
- Error case:
  - failed Research execution records a diagnosable failure shape

## Risks

- reliability work can spread too broadly if it is not kept tightly scoped to the Research baseline for Stage A

## Rollback Plan

- revert the new Research trust baseline while keeping the Stage A task structure and Research workflow work intact

## Execution Status

- Status: planned
- Notes: this is the required Platform Reliability companion task for the first Stage A Research wave
