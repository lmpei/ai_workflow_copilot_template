# Task: phase4-01-trace-and-observability-model

## Goal

Extend the trace model so Phase 4 can persist richer observability data for chat, tasks, agent runs, tool calls, and eval execution.

## Project Phase

- Phase: Phase 4
- Scenario module: shared platform core

## Why

Phase 4 needs a consistent trace backbone before analytics and evaluation results can be trusted or correlated across platform surfaces.

## Context

The repository already persists chat/task traces and basic metrics. Phase 4 should deepen those platform primitives without introducing external observability systems yet.

## Flow Alignment

- Flow A / B / C / D: Flow D primarily, with supporting links to Flows B and C
- Related APIs: `metrics`, future `evals`
- Related schema or storage changes: `traces`

## Dependencies

- Prior task: Phase 3 handoff complete
- Blockers: none

## Scope

Allowed files:

- `server/app/models/`
- `server/app/repositories/`
- `server/app/services/trace_service.py`
- `server/alembic/`
- `server/tests/`

Disallowed files:

- `web/`
- `server/app/workers/`
- `server/app/agents/`
- `server/app/api/routes/`

## Deliverables

- Code changes:
  - Extend trace storage for richer observability links and payloads
  - Add repository/service helpers for querying traces by platform object and workspace
  - Keep PostgreSQL as the source of truth
- Test changes:
  - Add trace persistence and aggregation tests for new fields
- Docs changes:
  - None required in this task

## Acceptance Criteria

- Traces can link to `task_id`, `agent_run_id`, `tool_call_id`, and `eval_run_id`
- Trace payloads can store latency, token, cost, error, and retrieval metadata consistently
- Existing trace-backed metrics behavior remains compatible
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

- Normal case: persist a trace linked to a task and agent run
- Edge case: store trace records with optional related ids omitted
- Error case: invalid trace linkage or malformed state is rejected safely

## Risks

- Over-designing trace schema too early could slow down Phase 4 delivery

## Rollback Plan

- Revert the migration and trace model changes; keep existing Phase 3 trace behavior intact
