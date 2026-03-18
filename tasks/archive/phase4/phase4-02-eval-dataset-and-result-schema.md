# Task: phase4-02-eval-dataset-and-result-schema

## Goal

Create the minimum evaluation data model needed for datasets, cases, runs, and results.

## Project Phase

- Phase: Phase 4
- Scenario module: shared platform core

## Why

Phase 4 needs durable evaluation primitives so quality review is not tied to ad hoc scripts or in-memory runs.

## Context

The initial Phase 4 target is retrieval-backed chat. The repository does not yet have first-class evaluation entities.

## Flow Alignment

- Flow A / B / C / D: Flow D
- Related APIs: future `evals`
- Related schema or storage changes:
  - `eval_datasets`
  - `eval_cases`
  - `eval_runs`
  - `eval_results`

## Dependencies

- Prior task: `phase4-01-trace-and-observability-model`
- Blockers: none

## Scope

Allowed files:

- `server/app/models/`
- `server/app/repositories/`
- `server/alembic/`
- `server/tests/`

Disallowed files:

- `web/`
- `server/app/workers/`
- `server/app/agents/`
- `server/app/api/routes/`

## Deliverables

- Code changes:
  - Add ORM models and migrations for evaluation datasets, cases, runs, and results
  - Add repository helpers for create/get/list/update flows
  - Define minimal status model for eval runs
- Test changes:
  - Add repository tests for dataset, case, run, and result persistence
- Docs changes:
  - None required in this task

## Acceptance Criteria

- Evaluation datasets and cases can be persisted and retrieved
- Eval runs can track status and summary fields
- Eval results can persist per-case output and scores
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

- Normal case: create dataset with cases, run, and results
- Edge case: empty dataset can still exist but cannot produce a successful run
- Error case: invalid status transitions are rejected

## Risks

- If case shape is too narrow, later task/agent evals may require noisy migrations

## Rollback Plan

- Revert eval-related models and migrations while leaving existing trace/task models intact
