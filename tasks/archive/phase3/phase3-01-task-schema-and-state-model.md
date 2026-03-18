# Task: phase3_task_schema_and_state_model

## Goal

Add the Phase 3 persistence model for tasks, agent runs, and tool calls with the smallest viable status machines.

## Project Phase

- Phase: `Phase 3`
- Scenario module: `shared platform core`

## Why

Phase 3 needs durable platform primitives before workers, agents, or frontend task views can exist. Task execution cannot rely on Redis memory alone.

## Context

Relevant specs:

- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`

Implementation defaults for this task:

- PostgreSQL remains the source of truth for task state and results
- `tasks` states:
  - `pending`
  - `running`
  - `done`
  - `failed`
- `agent_runs` states:
  - `pending`
  - `running`
  - `completed`
  - `failed`
- `tool_calls` states:
  - `pending`
  - `running`
  - `completed`
  - `failed`

## Flow Alignment

- Flow C: create task -> run agent -> persist tool calls -> save result
- Related APIs:
  - future `POST /api/v1/workspaces/{id}/tasks`
  - future `GET /api/v1/tasks/{id}`
  - future `GET /api/v1/workspaces/{id}/tasks`
- Related schema or storage changes:
  - `tasks`
  - `agent_runs`
  - `tool_calls`

## Dependencies

- Prior task:
  - `Phase 2` complete
- Blockers:
  - none

## Scope

Allowed files:

- `server/app/models/`
- `server/app/repositories/`
- `server/app/core/`
- `server/alembic/`
- `server/tests/`

Disallowed files:

- `web/`
- `server/app/workers/`
- `server/app/agents/`
- `server/app/api/routes/`

## Deliverables

- Code changes:
  - add ORM models and migrations for `tasks`, `agent_runs`, and `tool_calls`
  - add repository helpers for create/read/update/status transitions
  - add minimal state validation helpers
- Test changes:
  - add repository and migration coverage for the new models
- Docs changes:
  - none

## Acceptance Criteria

- Tasks, agent runs, and tool calls can be created and updated in PostgreSQL
- Minimal legal state transitions are enforced
- Task output and error fields are persisted
- No worker, API, or frontend behavior is introduced in this task

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python -m ruff check .`
  - `..\.venv\Scripts\python -m mypy app`
  - `..\.venv\Scripts\python -m pytest`
- Frontend:
  - none

## Tests

- Normal case: create a task, agent run, and tool call and move them through valid states
- Edge case: persist task results and tool outputs with structured JSON payloads
- Error case: invalid state transition is rejected

## Risks

- Over-designing the state model here will slow down worker and agent implementation in later Phase 3 tasks

## Rollback Plan

- revert the new models, migration, and repositories while leaving existing Phase 2 data untouched
