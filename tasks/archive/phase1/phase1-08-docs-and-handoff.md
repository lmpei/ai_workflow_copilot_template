# Task: phase1_docs_and_handoff

## Goal

Update project docs, verification notes, and handoff status so the repository truthfully reflects completed Phase 1 behavior.

## Project Phase

- Phase: `Phase 1`
- Scenario module: `shared platform core`

## Why

The repository currently states it is in Phase 0. Once the Phase 1 platform MVP is complete, the docs must reflect reality without overstating Phase 2+ capabilities.

## Context

Relevant specs:

- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`
- `README.md`

Current state:

- current docs explicitly identify the repo as `Phase 0: Scaffold & Alignment`
- Phase 1 completion will change the project status and demo path

## Flow Alignment

- Flow A / B / D: documents, chat, trace, and metrics are now demoable
- Related APIs: `auth`, `workspaces`, `documents`, `chat`, `metrics`
- Related schema or storage changes: none

## Dependencies

- Prior task:
  - `phase1_db_foundation`
  - `phase1_auth_boundary`
  - `phase1_workspace_persistence`
  - `phase1_document_surface`
  - `phase1_chat_contract_and_trace`
  - `phase1_metrics_minimal_loop`
  - `phase1_frontend_mvp_integration`
- Blockers: none

## Scope

Allowed files:

- `README.md`
- `docs/PROJECT_GUIDE.md`
- `docs/prd/PLATFORM_PRD.md`
- Phase 1-related test files if small coverage gaps remain

Disallowed files:

- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `server/app/api/routes/agents.py`
- `server/app/workers/`

## Deliverables

- Code changes:
  - none required beyond final test cleanup if needed
- Test changes:
  - close any small test gaps discovered during handoff
- Docs changes:
  - update current project status to `Phase 1`
  - document the current runnable MVP flow
  - clearly mark Phase 2/3/4/5 capabilities as not implemented yet

## Acceptance Criteria

- Docs reflect the actual implemented Phase 1 feature set
- README explains the current demo path from auth to workspace to document to chat to metrics
- No document claims real RAG, workers, agents, or eval pipelines are complete
- Verification instructions remain accurate on Windows and Docker workflows

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

- Normal case: documented MVP flow matches actual behavior
- Edge case: docs still clearly separate implemented Phase 1 from future phases
- Error case: none

## Risks

- If the docs claim Phase 2 features too early, the project boundary will become ambiguous again

## Rollback Plan

- revert the status and handoff docs while preserving working Phase 1 code

