# Task: phase3_frontend_task_surface

## Goal

Add the minimum frontend task surface for creating tasks, polling/viewing status, and reading final results.

## Project Phase

- Phase: `Phase 3`
- Scenario module: `shared platform core`

## Why

Phase 3 needs a demoable UI for the task-and-agent platform primitives, not just backend APIs.

## Context

Relevant specs:

- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`

Implementation defaults for this task:

- supported task types:
  - `research_summary`
  - `workspace_report`
- keep the UI simple and TypeScript-first
- do not introduce a global state library

## Flow Alignment

- Flow C: create task -> inspect status -> inspect final output
- Related APIs:
  - `POST /api/v1/workspaces/{id}/tasks`
  - `GET /api/v1/tasks/{id}`
  - `GET /api/v1/workspaces/{id}/tasks`
- Related schema or storage changes:
  - none

## Dependencies

- Prior task:
  - `phase3_task_api_surface`
  - `phase3_task_execution_orchestration`
- Blockers:
  - none

## Scope

Allowed files:

- `web/app/`
- `web/components/`
- `web/lib/`

Disallowed files:

- `server/`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`

## Deliverables

- Code changes:
  - add task create form
  - add task list and task detail/result UI
  - connect tasks page to real APIs
- Test changes:
  - keep frontend verification at lint/build level
- Docs changes:
  - none

## Acceptance Criteria

- Users can create a supported task from the workspace tasks page
- Users can see task state transitions
- Users can open and read final task results
- No scenario-specific UI is introduced

## Verification Commands

- Backend:
  - none
- Frontend:
  - `cd web`
  - `npm.cmd run verify`

## Tests

- Normal case: create a task and see it appear in the list
- Edge case: refresh the page and keep the task list/result view working
- Error case: failed task state and error output are visible

## Risks

- Over-designing the task UI now will pull Phase 3 toward scenario modules too early

## Rollback Plan

- revert task UI files and keep backend task execution intact
