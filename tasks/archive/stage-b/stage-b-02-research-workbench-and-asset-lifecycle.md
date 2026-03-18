# Task: stage-b-02-research-workbench-and-asset-lifecycle

## Goal

Turn Stage B Research work from one-off task outputs into a reusable workbench and asset lifecycle.

## Project Stage

- Stage: Stage B
- Track: Research

## Why

Stage A proved that Research can produce structured reports, follow-up lineage, and grounded trust signals, but the
experience still centers on discrete task runs. Stage B should make Research feel like a reusable workspace workflow
rather than a sequence of isolated task results.

## Context

Relevant documents:

- `docs/prd/STAGE_B_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `docs/PROJECT_GUIDE.md`

Relevant runtime areas:

- `server/app/models/`
- `server/app/schemas/`
- `server/app/repositories/`
- `server/app/services/`
- `server/app/api/routes/`
- `server/tests/`
- `web/components/research/`
- `web/lib/`

## Flow Alignment

- Flow A / B / C / D: Flow B / C / D
- Related APIs: tasks, workspaces, research surfaces, any new Research asset endpoints needed
- Related schema or storage changes: Research brief/report asset lifecycle as needed

## Dependencies

- Prior task: `tasks/archive/stage-b/stage-b-01-task-stack-planning.md`
- Blockers: none

## Scope

Allowed files:

- `server/app/models/`
- `server/app/schemas/`
- `server/app/repositories/`
- `server/app/services/`
- `server/app/api/routes/`
- `server/tests/`
- `web/components/research/`
- `web/lib/`
- `docs/PROJECT_GUIDE.md`

Disallowed files:

- support or job module productization
- staging or deployment docs unrelated to Research workflow behavior

## Deliverables

- Code changes:
  - define the first persistent Research workbench or asset lifecycle primitives needed for Stage B
  - allow saved or revisable Research artifacts beyond a single task result when appropriate
  - expose the workflow clearly in the Research surface
- Test changes:
  - add or update coverage for saved, revised, or compared Research assets
- Docs changes:
  - update developer-facing docs if the canonical Research lifecycle changes

## Acceptance Criteria

- Research work is no longer represented only as one-off task outputs
- a user can reopen, revise, or continue a Research asset in a reusable workflow shape
- lineage and report-history expectations remain explicit enough for later eval and recovery work

## Verification Commands

- Backend:
  - `python -m compileall server/app server/tests`
  - `cd server`
  - `..\.venv\Scripts\python.exe -m pytest tests/test_research_assistant_service.py tests/test_tasks.py tests/test_agent_service.py tests/test_task_execution_service.py`
- Frontend:
  - `cmd /c npm --prefix web run verify`

## Tests

- Normal case:
  - a saved Research asset can be reopened and revised without losing structured history
- Edge case:
  - multiple related Research runs can still be distinguished cleanly
- Error case:
  - invalid or stale Research asset references are rejected clearly

## Risks

- adding a workbench lifecycle too aggressively could overfit the current UI before the asset model is stable

## Rollback Plan

- revert the Stage B Research workbench changes while preserving Stage A task/report flows and lineage support
