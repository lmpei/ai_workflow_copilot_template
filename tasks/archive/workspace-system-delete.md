# Task: Workspace System Delete

## Goal

Add one permanent system-level workspace delete path with explicit confirmation, owner-only authorization, and cleanup of workspace-associated data.

## Project Phase

- Phase: Post-Stage-K follow-up
- Scenario module: shared workspace navigation and lifecycle

## Why

Users can now find all workspaces again, but there is still no bounded way to remove stale workspaces. Old workspaces keep accumulating, and the user has explicitly confirmed that deleting a workspace should permanently remove the workspace plus its associated data.

## Context

Relevant modules, dependencies, and related specs:

- `server/app/api/routes/workspaces.py`
- `server/app/services/workspace_service.py`
- `server/app/repositories/workspace_repository.py`
- `server/tests/test_workspaces.py`
- `web/components/workspace/workspace-history-page.tsx`
- `web/lib/api.ts`

## Flow Alignment

- Flow A:
  - list all workspaces in one lightweight page
  - delete one workspace after explicit confirmation
- Flow B:
  - remove the workspace record and its associated data tree
- Related APIs:
  - `GET /workspaces`
  - `DELETE /workspaces/{workspace_id}`
- Related schema or storage changes:
  - no schema changes
  - cleanup includes database rows and uploaded workspace files

## Dependencies

- Prior task:
  - `tasks/ai-hot-tracker-422-and-workspace-history-entry.md`
- Blockers:
  - none inside the repo

## Scope

Allowed files:

- `server/app/api/routes/workspaces.py`
- `server/app/services/workspace_service.py`
- `server/app/repositories/workspace_repository.py`
- `server/tests/test_workspaces.py`
- `web/components/workspace/`
- `web/lib/`
- control-plane docs

Disallowed files:

- deployment and environment files
- unrelated module surfaces
- any unconfirmed soft-delete/archive redesign

## Deliverables

- Code changes:
  - backend delete route for workspaces
  - owner-only delete behavior
  - cleanup of workspace-associated records and uploaded files
  - lightweight frontend delete affordance with two-step confirmation
- Test changes:
  - backend workspace delete tests
  - frontend verify pass
- Docs changes:
  - update `STATUS.md` so the active destructive follow-up is explicit

## Acceptance Criteria

- authenticated owner can permanently delete a workspace from the lightweight workspace-history page
- deleting a workspace removes it from `/workspaces`
- deleted workspace can no longer be fetched
- non-owner or non-member cannot delete a workspace
- uploaded files that belong to the deleted workspace are removed from disk when present
- frontend and backend verification pass

## Verification Commands

- Backend:
  - `cd server`
  - `..\\.venv\\Scripts\\python.exe -m pytest tests`
- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - owner deletes a workspace and it disappears from the list
- Edge case:
  - deleting a workspace with no associated records still succeeds
- Error case:
  - deleting a workspace as another user returns not found

## Risks

- workspace data is spread across multiple tables, so deletion order must be explicit
- external vector-store cleanup may need best-effort handling if the vector backend is unavailable

## Rollback Plan

- remove the frontend delete affordance
- remove the workspace delete API route
- revert repository/service deletion logic
