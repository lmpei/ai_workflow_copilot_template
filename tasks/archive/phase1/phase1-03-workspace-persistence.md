# Task: phase1_workspace_persistence

## Goal

Replace in-memory workspace storage with PostgreSQL-backed workspace persistence tied to authenticated users.

## Project Phase

- Phase: `Phase 1`
- Scenario module: `shared platform core`

## Why

Workspace persistence is one of the explicit Phase 1 goals and is the platform container for documents, conversations, and metrics.

## Context

Relevant specs:

- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`

Current state:

- `workspaces` API already has CRUD contracts
- `server/app/repositories/workspace_repository.py` still uses an in-memory list
- `owner_id` is currently hard-coded to `demo-user`

## Flow Alignment

- Flow A / B: workspace is the shared scope boundary
- Related APIs:
  - `GET /api/v1/workspaces`
  - `POST /api/v1/workspaces`
  - `GET /api/v1/workspaces/{id}`
  - `PATCH /api/v1/workspaces/{id}`
- Related schema or storage changes: `workspaces`, `workspace_members`

## Dependencies

- Prior task:
  - `phase1_db_foundation`
  - `phase1_auth_boundary`
- Blockers: none

## Scope

Allowed files:

- `server/app/api/routes/workspaces.py`
- `server/app/models/workspace.py`
- `server/app/schemas/workspace.py`
- `server/app/repositories/workspace_repository.py`
- `server/app/services/workspace_service.py`

Disallowed files:

- `web/`
- `server/app/api/routes/documents.py`
- `server/app/services/retrieval_service.py`

## Deliverables

- Code changes:
  - replace in-memory workspace storage with repository-backed DB persistence
  - bind workspace ownership to the authenticated user
  - create owner membership records on workspace creation
  - restrict workspace read/update access to users with membership
- Test changes:
  - convert workspace tests to authenticated API flows
- Docs changes:
  - none required

## Acceptance Criteria

- Workspaces persist across app restarts
- `demo-user` is removed from runtime behavior
- Unauthenticated access is rejected
- Users can only list and fetch workspaces they belong to
- Delete, invite, and member-management APIs remain out of scope

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python -m ruff check .`
  - `..\.venv\Scripts\python -m mypy app`
  - `..\.venv\Scripts\python -m pytest`
- Frontend:
  - none

## Tests

- Normal case: authenticated user creates, lists, gets, and updates a workspace
- Edge case: same user can own multiple workspaces
- Error case: unauthorized or unknown workspace access returns the correct failure

## Risks

- Membership and ownership checks can become inconsistent if access rules are not centralized in the service/repository layer

## Rollback Plan

- revert repository and route changes and temporarily restore the in-memory workspace store
