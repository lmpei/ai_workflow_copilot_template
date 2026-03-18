# Task: phase4-04-eval-runner-and-worker-execution

## Goal

Run evaluation datasets asynchronously through Redis + ARQ and persist eval run state and per-case outputs.

## Project Phase

- Phase: Phase 4
- Scenario module: shared platform core

## Why

Evaluation should execute like a platform workflow, not as a synchronous HTTP request or one-off script.

## Context

The project already uses Redis + ARQ for task execution. Phase 4 should reuse the same worker foundation for eval runs.

## Flow Alignment

- Flow A / B / C / D: Flow D
- Related APIs: eval run creation from `phase4-03`
- Related schema or storage changes: `eval_runs`, `eval_results`, traces

## Dependencies

- Prior task:
  - `phase4-01-trace-and-observability-model`
  - `phase4-02-eval-dataset-and-result-schema`
  - `phase4-03-eval-api-surface`
- Blockers: none

## Scope

Allowed files:

- `server/app/core/`
- `server/app/services/`
- `server/app/workers/`
- `server/app/repositories/`
- `server/tests/`
- `docker-compose.yml`

Disallowed files:

- `web/`
- `server/app/agents/`

## Deliverables

- Code changes:
  - Add eval enqueue helpers and ARQ worker entrypoints
  - Execute eval cases asynchronously and persist run progress
  - Record eval traces during execution
- Test changes:
  - Add worker and orchestration tests for successful and failed eval runs
- Docs changes:
  - None required in this task

## Acceptance Criteria

- Eval runs can be enqueued and consumed by ARQ workers
- Run status moves through a minimal lifecycle and persists summary progress
- Per-case results are written to PostgreSQL
- Failures mark the run as failed and preserve error details
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

- Normal case: run a small dataset successfully through ARQ orchestration
- Edge case: dataset with one failing case still persists partial results and run status
- Error case: enqueue or worker execution failure marks the eval run failed

## Risks

- Long eval loops can blur worker/runtime boundaries if orchestration is not kept small and explicit

## Rollback Plan

- Revert eval worker integration while leaving dataset storage and APIs intact
