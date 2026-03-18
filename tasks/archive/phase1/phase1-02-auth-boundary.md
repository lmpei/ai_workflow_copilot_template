# Task: phase1_auth_boundary

## Goal

Implement registration, login, current-user lookup, and bearer-token protection for Phase 1 APIs.

## Project Phase

- Phase: `Phase 1`
- Scenario module: `shared platform core`

## Why

Phase 1 requires a real auth boundary. Without it, workspaces, documents, chat, and metrics remain anonymous demo endpoints instead of platform primitives.

## Context

Relevant specs:

- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`

Current state:

- `server/app/api/routes/auth.py` is scaffold-only
- `server/app/schemas/auth.py` already defines request/response contracts
- `server/app/core/security.py` already contains password hashing helpers

Implementation defaults for this task:

- Use bearer-token auth with JWT-style access tokens
- Implement `register`, `login`, and `me`
- Do not add refresh tokens in Phase 1

## Flow Alignment

- Flow B: user identity gates workspace and chat access
- Related APIs:
  - `POST /api/v1/auth/register`
  - `POST /api/v1/auth/login`
  - `GET /api/v1/auth/me`
- Related schema or storage changes: `users`

## Dependencies

- Prior task: `phase1_db_foundation`
- Blockers: none

## Scope

Allowed files:

- `server/app/api/routes/auth.py`
- `server/app/core/security.py`
- `server/app/models/user.py`
- `server/app/schemas/auth.py`
- `server/app/repositories/`
- `server/app/services/auth_service.py`

Disallowed files:

- `web/`
- `server/app/api/routes/documents.py`
- `server/app/api/routes/chat.py`

## Deliverables

- Code changes:
  - replace `501 scaffold` auth routes with real behavior
  - persist users with unique email addresses
  - issue access tokens on login
  - add current-user dependency for protected APIs
- Test changes:
  - add API tests for register, login, me, and auth failures
- Docs changes:
  - none required

## Acceptance Criteria

- A user can register with email, password, and name
- A user can log in and receive `LoginResponse`
- `/api/v1/auth/me` returns the authenticated user
- Protected Phase 1 APIs can reject missing or invalid tokens with `401`
- No social auth, refresh flow, or session-cookie flow is added

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python -m ruff check .`
  - `..\.venv\Scripts\python -m mypy app`
  - `..\.venv\Scripts\python -m pytest`
- Frontend:
  - none

## Tests

- Normal case: register -> login -> me
- Edge case: duplicate email registration is rejected
- Error case: wrong password and invalid token both fail correctly

## Risks

- Token format or dependency shape can drift from frontend needs if not kept aligned with existing auth schemas

## Rollback Plan

- revert auth route and service changes and temporarily restore auth scaffolds
