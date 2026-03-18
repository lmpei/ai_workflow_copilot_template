# Task: phase3_langgraph_agent_runtime

## Goal

Implement the first minimal LangGraph-based platform agent without introducing LangChain or scenario-specific modules.

## Project Phase

- Phase: `Phase 3`
- Scenario module: `shared platform core`

## Why

Phase 3 must prove that an agent runtime can orchestrate multiple steps and tools on top of the platform primitives already built in Phases 1 and 2.

## Context

Relevant specs:

- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`

Implementation defaults for this task:

- use LangGraph as the only orchestration framework
- do not introduce LangChain
- first agent: `workspace_research_agent`
- the graph should only handle:
  - state passing
  - simple decision flow
  - tool invocation
  - final output assembly

## Flow Alignment

- Flow C: create task -> agent plans minimal steps -> call tools -> assemble final result
- Related APIs:
  - indirectly used by future task execution
- Related schema or storage changes:
  - `agent_runs`

## Dependencies

- Prior task:
  - `phase3_task_schema_and_state_model`
  - `phase3_tool_registry`
- Blockers:
  - LangGraph dependency must be selected and installed

## Scope

Allowed files:

- `server/app/agents/`
- `server/app/services/`
- `server/app/repositories/`
- `server/requirements.txt`
- `server/tests/`

Disallowed files:

- `web/`
- `server/app/workers/`
- `server/app/api/routes/`
- `server/app/services/retrieval_service.py` except required integration touchpoints

## Deliverables

- Code changes:
  - add LangGraph runtime wiring for one platform agent
  - add graph state model
  - add agent-run persistence hooks
- Test changes:
  - add unit tests for the graph happy path and failure path
- Docs changes:
  - none

## Acceptance Criteria

- One LangGraph agent can execute a minimal tool-using workflow
- Agent run status is persisted from `pending` to `running` to `completed/failed`
- Final agent output is produced in a structured form
- No scenario-specific job/support/research business workflow is introduced

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python -m ruff check .`
  - `..\.venv\Scripts\python -m mypy app`
  - `..\.venv\Scripts\python -m pytest`
- Frontend:
  - none

## Tests

- Normal case: the graph runs through a simple workspace research flow and completes
- Edge case: the graph completes with minimal available context
- Error case: tool or node failure marks the agent run `failed`

## Risks

- Pulling in LangChain here would expand scope without solving a current Phase 3 problem

## Rollback Plan

- revert LangGraph runtime files and keep task/tool persistence available for later work
