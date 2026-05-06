# Task: AI hot tracker background agent run

## Goal

Move manual `AI hot tracker` generation off the browser request path and onto a durable background run with polling.

## Project Phase

- Phase: Phase 5 stabilization
- Scenario module: AI hot tracker

## Why

Public generation could finish on the server but still surface as `API unreachable` in the browser because the report was generated inside one long synchronous HTTP request. The product needs a durable run record, visible status, and honest failure state instead of making the browser wait for the full agent loop.

## Context

The hot-tracker loop already has source intake, ranking, clustering, delta, brief generation, tracking state, signal memory, follow-up, and evaluation. This task changes the delivery mechanics: manual run creation now returns a queued run immediately, while the worker completes the same canonical loop in the background.

## Flow Alignment

- Flow: workspace -> hot-tracker run -> ARQ worker -> saved brief -> run-bound follow-up
- Related APIs:
  - `POST /workspaces/{workspace_id}/ai-hot-tracker/runs`
  - `GET /ai-hot-tracker/runs/{run_id}`
  - `GET /workspaces/{workspace_id}/ai-hot-tracker/state`
- Related schema or storage changes:
  - `ai_hot_tracker_tracking_runs.started_at`
  - `ai_hot_tracker_tracking_runs.completed_at`
  - `ai_hot_tracker_tracking_runs.failed_at`
  - `ai_hot_tracker_tracking_runs.failure_stage`
  - `ai_hot_tracker_tracking_runs.trace_events_json`

## Dependencies

- Prior task: `tasks/archive/ai-hot-tracker-final-definition-source-of-truth.md`
- Blockers: none

## Scope

Allowed files:

- `server/app/models/`
- `server/app/repositories/`
- `server/app/schemas/`
- `server/app/services/ai_hot_tracker_tracking_service.py`
- `server/app/api/routes/research_analysis_runs.py`
- `server/app/workers/task_worker.py`
- `server/alembic/versions/`
- `server/tests/test_ai_hot_tracker_tracking_runs.py`
- `web/components/research/ai-hot-tracker-workspace.tsx`
- `web/lib/types.ts`
- control-plane docs

Disallowed files:

- deployment strategy files
- environment files
- unrelated module product surfaces

## Deliverables

- Code changes:
  - manual run creation now creates a `queued` run and enqueues `run_ai_hot_tracker_tracking_run`
  - worker execution updates the same run to `running`, then `completed`, `degraded`, or `failed`
  - run responses expose runtime timestamps, failure stage, and trace events
  - frontend polls the run detail endpoint until terminal status
- Test changes:
  - hot-tracker run tests now exercise queued creation plus worker execution
- Docs changes:
  - control-plane docs record background-run delivery as the current canonical path

## Acceptance Criteria

- Public generation no longer depends on a long browser-held POST request
- Running, degraded, and failed runs remain visible and inspectable
- Failed runs persist real `error_message` and `failure_stage`
- Existing scheduled sweeper behavior remains intact
- Frontend renders queued/running status and stops polling after terminal status

## Verification Commands

- Backend:
  - `cd server && ..\.venv\Scripts\python.exe -m pytest tests`
- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case: manual run is queued, worker completes it, and the brief renders
- Edge case: state and evaluation endpoints read the completed run after background execution
- Error case: enqueue or worker failure persists a failed run with trace and error details

## Risks

- Worker availability is now required for manual report completion in deployed environments.
- Existing local databases need the new Alembic migration before reading background-run fields.

## Rollback Plan

Revert the background-run commit and run Alembic downgrade for `20260426_0023` if the new delivery path causes production instability.
