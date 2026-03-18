# Task: phase1_frontend_mvp_integration

## Goal

Connect the existing frontend route shells to the real Phase 1 auth, workspace, document, chat, and metrics APIs.

## Project Phase

- Phase: `Phase 1`
- Scenario module: `shared platform core`

## Why

Phase 1 must be demoable as a platform MVP, not just as backend endpoints with static frontend placeholders.

## Context

Relevant specs:

- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`

Current state:

- `web/app/` contains page shells only
- `web/lib/api.ts` only wraps `/health`
- `web/lib/auth.ts` is placeholder-only

Implementation defaults for this task:

- Use browser-side bearer token storage in `localStorage`
- Use the existing App Router structure
- Avoid introducing a separate BFF or state-management library in Phase 1

## Flow Alignment

- Flow A / B / D
- Related APIs:
  - `auth`
  - `workspaces`
  - `documents`
  - `chat`
  - `metrics`
- Related schema or storage changes: none

## Dependencies

- Prior task:
  - `phase1_auth_boundary`
  - `phase1_workspace_persistence`
  - `phase1_document_surface`
  - `phase1_chat_contract_and_trace`
  - `phase1_metrics_minimal_loop`
- Blockers: none

## Scope

Allowed files:

- `web/app/`
- `web/components/`
- `web/lib/api.ts`
- `web/lib/auth.ts`
- `web/lib/types.ts`

Disallowed files:

- `server/app/api/routes/agents.py`
- `server/app/workers/`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`

## Deliverables

- Code changes:
  - connect login and register pages to real auth endpoints
  - add token/user helpers in `web/lib/auth.ts`
  - add authenticated API helpers in `web/lib/api.ts`
  - implement workspace list/create UI
  - implement document upload/list UI
  - implement chat submit/render UI
  - implement metrics display UI
- Test changes:
  - no new frontend test framework required in Phase 1
  - keep `lint + build` green
- Docs changes:
  - none required

## Acceptance Criteria

- A user can register and log in from the frontend
- A logged-in user can create a workspace
- A logged-in user can upload a document into a workspace
- A logged-in user can submit a chat prompt and see the response and `trace_id`
- A logged-in user can view workspace metrics
- UI polish, SSR auth guarding, and scenario-specific UX remain out of scope

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python -m ruff check .`
  - `..\.venv\Scripts\python -m mypy app`
  - `..\.venv\Scripts\python -m pytest`
- Frontend:
  - `cd web`
  - `npm.cmd run verify`

## Tests

- Normal case: register -> login -> create workspace -> upload document -> chat -> view metrics
- Edge case: page refresh preserves usable auth state
- Error case: `401` clears invalid auth state and requires re-login

## Risks

- `localStorage` is acceptable for Phase 1 MVP but will need a deliberate migration if the platform later moves to cookie-based auth

## Rollback Plan

- revert frontend integrations and temporarily restore route shells while preserving backend APIs
