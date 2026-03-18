# Task: phase2_frontend_rag_surface

## Goal

Update the frontend MVP to expose ingest status, reindex behavior, and retrieval-backed citations for workspace chat.

## Project Phase

- Phase: `Phase 2`
- Scenario module: `shared platform core`

## Why

Phase 2 must be demoable end to end. The UI needs to reflect ingest progress and grounded answer sources instead of Phase 1 placeholders.

## Context

Relevant specs:

- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`

Current state:

- document upload/list UI exists
- chat UI exists and shows answers plus `trace_id`
- the frontend does not show ingest status transitions or real sources yet

Implementation defaults for this task:

- keep the current App Router structure
- keep browser-based bearer session handling from Phase 1
- render document ingest status directly from the API
- render chat citations from `sources`
- keep UI scope pragmatic; avoid unrelated visual redesign

## Flow Alignment

- Flow A: upload -> index -> reflect status in documents UI
- Flow B: ask question -> show grounded answer and citations
- Related APIs:
  - `GET /api/v1/workspaces/{id}/documents`
  - `POST /api/v1/workspaces/{id}/documents/upload`
  - `POST /api/v1/documents/{id}/reindex`
  - `POST /api/v1/workspaces/{id}/chat`
- Related schema or storage changes:
  - frontend consumes document status and chat sources

## Dependencies

- Prior task:
  - `phase2_ingest_orchestration_and_reindex`
  - `phase2_retrieval_backed_chat`
- Blockers: none

## Scope

Allowed files:

- `web/app/`
- `web/components/`
- `web/lib/api.ts`
- `web/lib/types.ts`

Disallowed files:

- `server/`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`

## Deliverables

- Code changes:
  - show ingest status in the documents UI
  - add a reindex action in the documents UI
  - show grounded source references in chat results
  - keep auth/workspace/session behavior stable
- Test changes:
  - rely on `lint` and `build`; no new frontend test framework required
- Docs changes:
  - none required

## Acceptance Criteria

- Users can see whether a document is uploaded, indexing, indexed, or failed
- Users can trigger reindex from the UI
- Chat results display real source references from the backend
- No agent/task/evaluation UI is introduced in this task

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

- Normal case: an indexed document appears as indexed and chat shows one or more sources
- Edge case: a failed ingest status is visible and reindex can be triggered again
- Error case: backend retrieval or reindex errors are surfaced clearly in the UI

## Risks

- If the UI hides ingest state, Phase 2 demos will look flaky even when the pipeline is actually working

## Rollback Plan

- revert frontend status/citation rendering and restore the simpler Phase 1 UI
