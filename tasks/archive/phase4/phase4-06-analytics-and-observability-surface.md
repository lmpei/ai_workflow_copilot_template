# Task: phase4-06-analytics-and-observability-surface

## Goal

Expose richer Phase 4 analytics and observability data from traces and eval results.

## Project Phase

- Phase: Phase 4
- Scenario module: shared platform core

## Why

Phase 4 needs a consistent summary layer so users can inspect quality, latency, token usage, and pass/fail trends without direct database access.

## Context

The current platform already exposes basic workspace metrics from traces. This task should extend that layer with Phase 4 summary views, not replace it with an external monitoring stack.

## Flow Alignment

- Flow A / B / C / D: Flow D
- Related APIs:
  - `metrics`
  - `evals`
  - analytics summary endpoints as needed
- Related schema or storage changes: traces, eval results

## Dependencies

- Prior task:
  - `phase4-01-trace-and-observability-model`
  - `phase4-04-eval-runner-and-worker-execution`
  - `phase4-05-chat-evaluator-framework`
- Blockers: none

## Scope

Allowed files:

- `server/app/api/routes/`
- `server/app/services/`
- `server/app/repositories/`
- `server/app/schemas/`
- `server/tests/`

Disallowed files:

- `web/`
- external monitoring integrations

## Deliverables

- Code changes:
  - Extend analytics/metrics responses with Phase 4 summaries
  - Add eval summary queries and observability drill-down endpoints as needed
  - Keep PostgreSQL-backed aggregation as the source of truth
- Test changes:
  - Add aggregation tests for traces and eval results
- Docs changes:
  - None required in this task

## Acceptance Criteria

- Workspace analytics can summarize trace volume, latency, token usage, retrieval hit rate, and eval pass-rate style metrics
- Eval run summaries can be fetched through stable APIs
- Existing metrics contract remains compatible or is intentionally versioned
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

- Normal case: analytics endpoint returns non-zero summaries after traces and eval results exist
- Edge case: empty workspace still returns valid zero-state analytics
- Error case: cross-workspace analytics access returns `404`

## Risks

- If metrics definitions drift between traces and eval summaries, dashboard behavior will be confusing

## Rollback Plan

- Revert Phase 4 analytics additions and fall back to existing Phase 3 metrics behavior
