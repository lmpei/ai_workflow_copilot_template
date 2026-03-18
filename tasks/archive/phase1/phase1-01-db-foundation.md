# Task: phase1_db_foundation

## Goal

Establish the database, ORM, migration, and session foundation required for Phase 1 platform persistence.

## Project Phase

- Phase: `Phase 1`
- Scenario module: `shared platform core`

## Why

Phase 1 requires real persistence for auth, workspaces, documents, chat state, and traces. The current scaffold only exposes configuration placeholders and in-memory storage.

## Context

Relevant specs:

- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`

Current state:

- `server/app/core/database.py` only exposes parsed config
- `server/app/models/` contains dataclass scaffolds, not ORM models
- no migration tooling exists yet

Implementation defaults for this task:

- Use `SQLAlchemy` for ORM and sessions
- Use `Alembic` for migrations
- Keep PostgreSQL as the runtime database
- Keep tests runnable with a separate test DB or SQLite-compatible test setup

## Flow Alignment

- Flow A / B / D: supports document metadata, conversations, and traces as shared primitives
- Related APIs: `auth`, `workspaces`, `documents`, `chat`, `metrics`
- Related schema or storage changes: `users`, `workspaces`, `workspace_members`, `documents`, `conversations`, `messages`, `traces`

## Dependencies

- Prior task: none
- Blockers: none

## Scope

Allowed files:

- `server/app/core/`
- `server/app/models/`
- `server/app/repositories/`
- `server/requirements.txt`
- `server/migrations/` or `server/alembic*`

Disallowed files:

- `web/`
- `server/app/api/routes/agents.py`
- `server/app/workers/`

## Deliverables

- Code changes:
  - add SQLAlchemy engine, session factory, declarative base, and DB dependency helpers
  - add Alembic configuration and an initial migration
  - convert Phase 1 data entities to ORM-backed models
  - make repository code able to use DB sessions instead of in-memory globals
- Test changes:
  - add a database bootstrap smoke test
  - add at least one repository persistence smoke test
- Docs changes:
  - only minimal developer note updates if needed for migrations

## Acceptance Criteria

- The app can initialize a real DB connection using `DATABASE_URL`
- An initial migration creates the Phase 1 core tables
- ORM models exist for all Phase 1 persisted entities
- Later Phase 1 tasks no longer need in-memory workspace storage
- No RAG, worker, or agent runtime logic is introduced here

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python -m ruff check .`
  - `..\.venv\Scripts\python -m mypy app`
  - `..\.venv\Scripts\python -m pytest`
- Frontend:
  - none

## Tests

- Normal case: test DB initializes and tables can be created
- Edge case: empty database startup succeeds
- Error case: invalid `DATABASE_URL` fails clearly

## Risks

- ORM model naming can drift from existing Pydantic schema naming and create avoidable churn in later tasks

## Rollback Plan

- revert ORM, migration, and session changes and temporarily restore in-memory persistence boundaries
