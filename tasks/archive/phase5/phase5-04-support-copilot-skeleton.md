# Task: phase5-04-support-copilot-skeleton

## Goal

Create the minimum backend and frontend skeleton for the Support Copilot module using shared platform primitives.

## Project Phase

- Phase: Phase 5
- Scenario module: support

## Why

Support Copilot should demonstrate that a second scenario can plug into the same workspace, task, agent, and eval infrastructure without creating a parallel system.

## Context

This task should stay intentionally shallow: module configuration, one or two support task types, and a light product surface are enough.

## Flow Alignment

- Flow A / B / C / D: Flow B / C / D
- Related APIs: tasks, chat, evals, analytics
- Related schema or storage changes: support module task/result contracts

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
  - Add minimal support module task flow and UI skeleton
  - Reuse shared tasks/agents/evals primitives
- Test changes:
  - Add targeted API/service/UI coverage as needed
- Docs changes:
  - None required in this task

## Acceptance Criteria

- Support Copilot has a visible module entry and minimal executable flow
- Shared platform primitives remain the source of truth
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

- Normal case: support module task can be created and rendered
- Edge case: empty knowledge context still returns a bounded support result shape
- Error case: unsupported support action is rejected clearly

## Risks

- Ticketing or approval complexity could pull this task beyond the intended skeleton scope

## Rollback Plan

- Revert support-specific routes and UI while keeping shared module contracts intact
