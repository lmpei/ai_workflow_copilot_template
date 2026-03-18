# Task: phase3_tool_registry

## Goal

Create a static Python tool registry that LangGraph can use and that persists tool-call execution details.

## Project Phase

- Phase: `Phase 3`
- Scenario module: `shared platform core`

## Why

Phase 3 needs a predictable platform tool surface before a real agent can run. A static registry keeps scope small and auditable.

## Context

Relevant specs:

- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`

Implementation defaults for this task:

- use a static in-repo registry
- do not implement dynamic plugin loading
- initial tool set:
  - `search_documents`
  - `get_document`
  - `list_workspace_documents`

## Flow Alignment

- Flow C: agent chooses tool -> tool executes -> tool call is persisted
- Related APIs:
  - indirectly used by future agent/task execution APIs
- Related schema or storage changes:
  - `tool_calls`

## Dependencies

- Prior task:
  - `phase3_task_schema_and_state_model`
- Blockers:
  - Phase 2 retrieval and document primitives must remain stable

## Scope

Allowed files:

- `server/app/agents/`
- `server/app/services/`
- `server/app/repositories/`
- `server/app/schemas/`
- `server/tests/`

Disallowed files:

- `web/`
- `server/app/workers/`
- `server/app/api/routes/`

## Deliverables

- Code changes:
  - add static tool registry definitions
  - add tool invocation helpers
  - persist tool call lifecycle and inputs/outputs
- Test changes:
  - add registry lookup and tool execution tests
- Docs changes:
  - none

## Acceptance Criteria

- Tools can be resolved by stable name
- Tool calls persist status, input, output, and latency
- Initial tools operate inside workspace scope
- No dynamic plugin system is introduced

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python -m ruff check .`
  - `..\.venv\Scripts\python -m mypy app`
  - `..\.venv\Scripts\python -m pytest`
- Frontend:
  - none

## Tests

- Normal case: resolve a tool by name and persist a completed tool call
- Edge case: tool output contains structured JSON payloads
- Error case: unknown tool name or tool failure is persisted as `failed`

## Risks

- Letting tool definitions drift away from repository/service boundaries will make later agent behavior hard to reason about

## Rollback Plan

- revert registry and tool-call execution helpers while keeping task models intact
