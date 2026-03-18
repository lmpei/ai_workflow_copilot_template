# Task: phase4-03-eval-api-surface

## Goal

Expose the minimum API surface for creating and viewing evaluation datasets and runs.

## Project Phase

- Phase: Phase 4
- Scenario module: shared platform core

## Why

Phase 4 should let the frontend and future reviewers work through stable eval APIs instead of direct database manipulation.

## Context

The first evaluation target is retrieval-backed chat. APIs should stay workspace-scoped and reuse existing auth patterns.

## Flow Alignment

- Flow A / B / C / D: Flow D
- Related APIs:
  - `POST /api/v1/workspaces/{id}/evals/datasets`
  - `GET /api/v1/workspaces/{id}/evals/datasets`
  - `POST /api/v1/workspaces/{id}/evals/runs`
  - `GET /api/v1/evals/runs/{id}`
- Related schema or storage changes: eval entities from `phase4-02`

## Dependencies

- Prior task: `phase4-02-eval-dataset-and-result-schema`
- Blockers: none

## Scope

Allowed files:

- `server/app/api/routes/`
- `server/app/schemas/`
- `server/app/services/`
- `server/app/repositories/`
- `server/tests/`

Disallowed files:

- `web/`
- `server/app/workers/`
- `server/app/agents/`

## Deliverables

- Code changes:
  - Add workspace-scoped eval dataset and eval run APIs
  - Reuse current auth and membership rules
  - Keep routes thin and business logic in services
- Test changes:
  - API tests for create/list/get flows and auth errors
- Docs changes:
  - None required in this task

## Acceptance Criteria

- Authenticated users can create eval datasets and runs inside accessible workspaces
- Users can view dataset lists and run details
- Non-members get `404`
- Invalid dataset/run payloads return clear `400` errors
- Tests pass
- Lint passes
- Type checks pass

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python -m ruff check .`
  - `..\.venv\Scripts\python -m mypy app`
  - `..\.venv\Scripts\python -m pytest`
- Frontend:
  - None

## Tests

- Normal case: create dataset, create run, fetch run details
- Edge case: dataset with multiple cases lists correctly
- Error case: unauthorized or cross-workspace access returns `401/404`

## Risks

- Letting API payloads drift away from eval persistence shapes would create avoidable translation complexity

## Rollback Plan

- Revert the eval routes/schemas/services while keeping the underlying data model in place if needed
