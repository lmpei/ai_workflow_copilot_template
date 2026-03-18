# Task: phase5-06-scenario-evals-and-quality-baselines

## Goal

Extend the Phase 4 evaluation framework so each scenario module can define and run module-specific eval datasets and quality checks.

## Project Phase

- Phase: Phase 5
- Scenario module: shared scenario evaluation

## Why

Phase 5 should not only add scenario flows; it should also prove those flows can be measured with the same evaluation and observability platform.

## Context

This task should reuse the existing eval dataset, eval run, and evaluator framework. The main change is scenario-specific cases, rubrics, and result views.

## Flow Alignment

- Flow A / B / C / D: Flow D
- Related APIs: evals, analytics, traces
- Related schema or storage changes: scenario-specific eval metadata and result summaries

## Dependencies

- Prior task:
  - `phase5-02-research-assistant-backend-mvp`
  - `phase5-04-support-copilot-skeleton`
  - `phase5-05-job-assistant-skeleton`
- Blockers: none

## Scope

Allowed files:

- `server/app/services/`
- `server/app/schemas/`
- `server/app/repositories/`
- `server/tests/`
- `web/app/`
- `web/components/`
- `web/lib/`

Disallowed files:

- `server/app/workers/`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`

## Deliverables

- Code changes:
  - Add scenario-specific eval dataset conventions and evaluator hooks
  - Surface scenario-level quality summaries in the frontend
- Test changes:
  - Add eval coverage for at least one scenario case per module
- Docs changes:
  - None required in this task

## Acceptance Criteria

- Research, support, and job modules can be evaluated through the shared eval framework
- Scenario-level quality summaries are visible without introducing a separate eval system
- Tests pass
- Lint passes
- Type checks pass
- Frontend verify/build passes

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python -m ruff check .`
  - `..\.venv\Scripts\python -m mypy app`
  - `..\.venv\Scripts\python -m pytest`
- Frontend:
  - `cd web`
  - `npm.cmd run verify`

## Tests

- Normal case: a scenario-specific eval run produces scores and pass/fail outputs
- Edge case: empty scenario dataset renders clearly without breaking the eval framework
- Error case: unsupported scenario evaluator input fails cleanly

## Risks

- Building a separate evaluation subsystem for each scenario would break platform consistency

## Rollback Plan

- Revert scenario-specific eval hooks while keeping the shared Phase 4 evaluation framework intact
