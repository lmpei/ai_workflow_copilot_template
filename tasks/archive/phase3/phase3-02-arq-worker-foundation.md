# Task: phase3_arq_worker_foundation

## Goal

Introduce Redis-backed ARQ workers and prove that a queued background job can update task state in PostgreSQL.

## Project Phase

- Phase: `Phase 3`
- Scenario module: `shared platform core`

## Why

Phase 3 requires asynchronous execution, but the project should avoid a heavy scheduling stack. ARQ is the minimum worker layer that matches the current FastAPI + Redis architecture.

## Context

Relevant specs:

- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`

Implementation defaults for this task:

- queue backend: Redis
- worker framework: ARQ
- PostgreSQL remains the source of truth for task state
- worker jobs should update `tasks` from `pending` to `running` to `done/failed`

## Flow Alignment

- Flow C: create task -> enqueue -> worker consumes -> persist state updates
- Related APIs:
  - indirectly used by future task-create endpoint
- Related schema or storage changes:
  - Redis queue wiring
  - task execution status updates

## Dependencies

- Prior task:
  - `phase3_task_schema_and_state_model`
- Blockers:
  - Redis must be reachable in local Docker and test environments

## Scope

Allowed files:

- `server/app/core/`
- `server/app/workers/`
- `server/app/services/`
- `server/app/repositories/`
- `server/requirements.txt`
- `server/tests/`
- `docker-compose.yml`

Disallowed files:

- `web/`
- `server/app/agents/`
- `server/app/api/routes/agents.py`

## Deliverables

- Code changes:
  - add ARQ configuration and worker entrypoint
  - add enqueue helper
  - add one minimal background job that updates persisted task state
- Test changes:
  - add worker-facing unit/integration tests with Redis calls mocked where needed
- Docs changes:
  - update local setup notes only if ARQ requires new commands or env values

## Acceptance Criteria

- A task can be enqueued into Redis from application code
- An ARQ worker can consume the job and update task state in PostgreSQL
- Worker errors mark the task as `failed`
- No agent logic is introduced yet

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python -m ruff check .`
  - `..\.venv\Scripts\python -m mypy app`
  - `..\.venv\Scripts\python -m pytest`
- Frontend:
  - none

## Tests

- Normal case: enqueue a task and confirm the worker marks it `done`
- Edge case: worker can process multiple tasks sequentially without corrupting state
- Error case: worker exception marks the task `failed`

## Risks

- Leaking queue state into the API or frontend too early will blur the separation between transient queue state and persisted task state

## Rollback Plan

- revert ARQ wiring and leave the task schema intact for later Phase 3 work
