# Task: phase3_task_api_surface

## Goal

Expose the minimal authenticated task API for creating tasks and reading task status/results.

## Project Phase

- Phase: `Phase 3`
- Scenario module: `shared platform core`

## Why

Workers and agents need a stable task boundary, and the frontend needs an API contract to create and inspect tasks.

## Context

Relevant specs:

- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`

Implementation defaults for this task:

- supported task types:
  - `research_summary`
  - `workspace_report`
- task creation writes a PostgreSQL row first, then enqueues background execution
- workspace membership controls task visibility

## Flow Alignment

- Flow C: create task -> persist task -> queue execution -> inspect state/result
- Related APIs:
  - `POST /api/v1/workspaces/{id}/tasks`
  - `GET /api/v1/tasks/{id}`
  - `GET /api/v1/workspaces/{id}/tasks`
- Related schema or storage changes:
  - request/response schemas for task creation and task reads

## Dependencies

- Prior task:
  - `phase3_task_schema_and_state_model`
  - `phase3_arq_worker_foundation`
- Blockers:
  - none

## Scope

Allowed files:

- `server/app/api/routes/tasks.py`
- `server/app/schemas/`
- `server/app/services/`
- `server/app/repositories/`
- `server/tests/`

Disallowed files:

- `web/`
- `server/app/agents/`
- `server/app/workers/` except existing enqueue integration points

## Deliverables

- Code changes:
  - implement create/list/detail task APIs
  - validate task types and workspace scope
  - enqueue task execution after persistence
- Test changes:
  - add API tests for auth, membership, create, list, and detail
- Docs changes:
  - none

## Acceptance Criteria

- Authenticated users can create tasks in their workspaces
- Authenticated users can list and inspect only their accessible tasks
- New tasks start as `pending`
- Unsupported task types are rejected with a stable error response

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python -m ruff check .`
  - `..\.venv\Scripts\python -m mypy app`
  - `..\.venv\Scripts\python -m pytest`
- Frontend:
  - none

## Tests

- Normal case: create a `research_summary` task and fetch it by id
- Edge case: list multiple tasks in one workspace
- Error case: unauthorized or foreign-workspace task access is rejected

## Risks

- Mixing task-creation logic with worker logic here will make API handlers too fat

## Rollback Plan

- revert task routes and schemas while preserving persisted task data
