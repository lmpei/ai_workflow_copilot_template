# Task: phase3_task_execution_orchestration

## Goal

Connect task creation, ARQ workers, LangGraph agent runs, and tool-call persistence into one real execution pipeline.

## Project Phase

- Phase: `Phase 3`
- Scenario module: `shared platform core`

## Why

This is the task that proves the Phase 3 platform primitives actually work together as one task-and-agent system.

## Context

Relevant specs:

- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`

Implementation defaults for this task:

- queue: Redis
- worker framework: ARQ
- runtime: LangGraph only
- first supported task types:
  - `research_summary`
  - `workspace_report`

## Flow Alignment

- Flow C: create task -> enqueue -> worker starts agent -> tools execute -> final result saved
- Related APIs:
  - `POST /api/v1/workspaces/{id}/tasks`
  - `GET /api/v1/tasks/{id}`
  - `GET /api/v1/workspaces/{id}/tasks`
- Related schema or storage changes:
  - `tasks`
  - `agent_runs`
  - `tool_calls`

## Dependencies

- Prior task:
  - `phase3_arq_worker_foundation`
  - `phase3_task_api_surface`
  - `phase3_tool_registry`
  - `phase3_langgraph_agent_runtime`
- Blockers:
  - none

## Scope

Allowed files:

- `server/app/services/`
- `server/app/workers/`
- `server/app/repositories/`
- `server/app/agents/`
- `server/app/api/routes/tasks.py`
- `server/tests/`

Disallowed files:

- `web/`
- `server/app/api/routes/agents.py`
- `server/app/services/eval_service.py`

## Deliverables

- Code changes:
  - orchestrate end-to-end task execution
  - worker starts persisted agent run
  - tool calls are persisted during execution
  - task output and errors are saved to PostgreSQL
- Test changes:
  - add orchestration tests covering end-to-end task execution
- Docs changes:
  - none

## Acceptance Criteria

- The system can run:
  - create task
  - execute worker
  - run agent
  - persist tool calls
  - save final result
- Successful execution marks the task `done`
- Failed execution marks the task `failed`
- Final output is retrievable from task APIs

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python -m ruff check .`
  - `..\.venv\Scripts\python -m mypy app`
  - `..\.venv\Scripts\python -m pytest`
- Frontend:
  - none

## Tests

- Normal case: `research_summary` executes and stores final output
- Edge case: `workspace_report` executes with limited indexed content but still completes
- Error case: agent or tool failure marks task and agent run as failed

## Risks

- If orchestration logic leaks across routes, workers, and agents without a single service boundary, Phase 3 will become hard to maintain quickly

## Rollback Plan

- revert worker-to-agent orchestration while preserving task API and schema work
