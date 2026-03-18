# Task: phase5-05-job-assistant-skeleton

## Goal

Create the minimum backend and frontend skeleton for the Job Assistant module using shared platform primitives.

## Project Phase

- Phase: Phase 5
- Scenario module: job

## Why

Job Assistant should prove that a more structured scenario can still reuse the same platform without forcing a separate workflow stack.

## Context

This task should stay lightweight: one or two job-oriented task types, minimal structured outputs, and a thin frontend entry are enough for Phase 5.

## Flow Alignment

- Flow A / B / C / D: Flow B / C / D
- Related APIs: documents, tasks, evals, analytics
- Related schema or storage changes: job module task/result contracts

## Dependencies

- Prior task:
  - `phase5-01-module-configuration-and-scenario-contracts`
  - `phase5-03-research-assistant-frontend-surface`
- Blockers: none

## Scope

Allowed files:

- `server/app/api/routes/`
- `server/app/services/`
- `server/app/agents/`
- `server/app/schemas/`
- `server/tests/`
- `web/app/`
- `web/components/`
- `web/lib/`

Disallowed files:

- `server/app/workers/`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`

## Deliverables

- Code changes:
  - Add minimal job module task flow and UI skeleton
  - Reuse shared tasks/agents/evals primitives
- Test changes:
  - Add targeted API/service/UI coverage as needed
- Docs changes:
  - None required in this task

## Acceptance Criteria

- Job Assistant has a visible module entry and minimal executable flow
- Structured result payload remains compatible with shared task handling
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

- Normal case: job module task can be created and rendered
- Edge case: limited source data still returns a bounded result shape
- Error case: invalid job-specific task input is rejected clearly

## Risks

- Pulling in resume/JD deep parsing too early would expand beyond the intended Phase 5 skeleton

## Rollback Plan

- Revert job-specific routes and UI while keeping shared module contracts intact
