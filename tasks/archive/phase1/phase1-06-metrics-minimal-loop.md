# Task: phase1_metrics_minimal_loop

## Goal

Replace fixed metrics placeholders with a real workspace-level aggregation over stored traces.

## Project Phase

- Phase: `Phase 1`
- Scenario module: `shared platform core`

## Why

Phase 1 explicitly requires a trace and metrics minimal loop. Without real aggregation, analytics remains only a UI placeholder.

## Context

Relevant specs:

- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`

Current state:

- `/api/v1/workspaces/{id}/metrics` returns hard-coded zero values
- no trace-backed aggregation exists

Implementation defaults for this task:

- Aggregate only from `traces`
- Keep `task_success_rate` fixed at `0.0` until Phase 3 tasks exist
- Count retrieval hits using non-empty trace response sources

## Flow Alignment

- Flow D: expose minimal observability over real chat traces
- Related APIs:
  - `GET /api/v1/workspaces/{id}/metrics`
- Related schema or storage changes: `traces`

## Dependencies

- Prior task: `phase1_chat_contract_and_trace`
- Blockers: none

## Scope

Allowed files:

- `server/app/api/routes/metrics.py`
- `server/app/services/trace_service.py`
- `server/app/repositories/`

Disallowed files:

- `web/`
- `server/app/api/routes/tasks.py`
- `server/app/api/routes/evals.py`

## Deliverables

- Code changes:
  - replace fixed snapshot behavior with workspace-scoped trace aggregation
  - compute:
    - `total_requests`
    - `avg_latency_ms`
    - `retrieval_hit_count`
    - `token_usage`
    - `task_success_rate`
  - enforce auth and workspace access checks
- Test changes:
  - add metrics tests for empty and populated trace sets
- Docs changes:
  - none required

## Acceptance Criteria

- Empty workspaces return zeroed metrics
- Workspaces with real traces return non-zero aggregated values where applicable
- Metrics depend only on persisted data
- No task, agent, or eval metrics are introduced yet

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python -m ruff check .`
  - `..\.venv\Scripts\python -m mypy app`
  - `..\.venv\Scripts\python -m pytest`
- Frontend:
  - none

## Tests

- Normal case: multiple traces aggregate to stable metrics
- Edge case: no traces returns all-zero metrics
- Error case: unauthorized workspace access is rejected

## Risks

- If metric definitions are not kept stable now, Phase 1 frontend analytics integration will churn unnecessarily

## Rollback Plan

- revert metrics aggregation and temporarily restore fixed placeholder values
