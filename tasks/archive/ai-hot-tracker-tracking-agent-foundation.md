# Task: AI Hot Tracker Tracking Agent Foundation

## Goal

Turn `AI 热点追踪` from a one-shot report page into a workspace-level continuous tracking agent with a persisted tracking profile, durable tracking runs, grounded follow-ups, and run-to-run change detection.

## Project Phase

- Phase: Post-Stage-K bounded follow-through
- Scenario module: research

## Why

The current `AI 热点追踪` flow still centers one manual report generation and optional saved records. That is not enough for a product that is supposed to feel like a real agent system. The module needs one durable container model inside the workspace, one persisted run history, one grounded follow-up thread per run, and one honest way to compare the latest run against the prior run.

## Context

Relevant modules, dependencies, and related specs:

- `server/app/services/ai_hot_tracker_source_service.py`
- `server/app/services/ai_hot_tracker_report_service.py`
- `server/app/services/ai_hot_tracker_follow_up_service.py`
- `server/app/services/ai_frontier_research_record_service.py`
- `server/app/repositories/workspace_repository.py`
- `server/app/schemas/ai_frontier_research.py`
- `web/components/research/ai-hot-tracker-workspace.tsx`
- `web/components/workspace/workspace-workbench-route.tsx`

## Flow Alignment

- Flow A:
  - workspace carries one default `tracking_profile` inside `module_config_json`
- Flow B:
  - manual tracking creates one persisted `tracking_run`
- Flow C:
  - report generation still runs from normalized source items into one structured schema path
- Flow D:
  - follow-up is bound to the selected run and its sources, not generic chat
- Related APIs:
  - add AI hot tracker run history APIs
  - add run-bound follow-up API
  - keep the module on one canonical workspace path
- Related schema or storage changes:
  - add durable `ai_hot_tracker_tracking_runs`
  - expose tracking profile, change summary, and run history to the frontend

## Dependencies

- Prior task:
  - `tasks/ai-hot-tracker-content-pipeline-rebuild.md`
- Blockers:
  - none inside the repo

## Scope

Allowed files:

- `server/app/api/routes/`
- `server/app/models/`
- `server/app/repositories/`
- `server/app/schemas/`
- `server/app/services/`
- `server/alembic/versions/`
- `server/tests/`
- `web/components/research/`
- `web/components/workspace/`
- `web/lib/`
- control-plane docs

Disallowed files:

- deployment and environment files
- module product names
- unrelated support/job workflow files

## Deliverables

- Code changes:
  - research module default config includes an AI hot tracker tracking profile
  - AI hot tracker run persistence with report payload, source payload, follow-ups, and delta summary
  - manual run creation API, run list API, run fetch API, run delete API
  - run-bound follow-up API
  - AI hot tracker frontend consumes tracking runs instead of optional saved records
- Test changes:
  - backend tests for first run, delta detection, and grounded follow-up persistence
  - frontend verify pass
- Docs changes:
  - update control-plane docs to reflect the new durable tracking model

## Acceptance Criteria

- Works correctly
- Tests pass
- Lint passes
- Type checks pass
- Build impact is addressed
- `AI 热点追踪` workspaces persist tracking runs and do not rely on a save-first report flow
- follow-up answers are bound to the selected run context

## Verification Commands

- Backend:
  - `cd server`
  - `..\\.venv\\Scripts\\python.exe -m pytest tests`
- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - first tracking run creates one durable run and report
- Edge case:
  - second tracking run compares against the previous run and marks change state correctly
- Error case:
  - partial source failure or report degradation still persists one honest run with the real degraded reason

## Risks

- Existing saved-record code can drift from the new run model if both stay active too long
- Source diff logic can be too noisy if it compares raw URLs without later clustering
- UI complexity can creep back if history, report, and follow-up do not share the same selected run state

## Rollback Plan

- Revert the AI hot tracker run APIs and frontend integration to the earlier report-only path
- Keep the older record endpoints intact until the new run flow is verified
