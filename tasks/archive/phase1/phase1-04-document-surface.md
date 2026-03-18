# Task: phase1_document_surface

## Goal

Implement the Phase 1 documents API surface with real file upload and document metadata persistence.

## Project Phase

- Phase: `Phase 1`
- Scenario module: `shared platform core`

## Why

Phase 1 must expose a real document surface before Phase 2 can add parsing, chunking, embeddings, and retrieval.

## Context

Relevant specs:

- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`

Current state:

- `server/app/api/routes/documents.py` is scaffold-only
- `server/app/schemas/document.py` already defines a response model
- no document persistence or file storage exists yet

Implementation defaults for this task:

- Support single-file multipart upload
- Save uploaded files to local disk for Phase 1
- Persist document metadata in PostgreSQL
- Keep document status at `uploaded`
- Keep `reindex` as a lightweight state-transition endpoint only

## Flow Alignment

- Flow A: upload file -> create metadata
- Related APIs:
  - `POST /api/v1/workspaces/{id}/documents/upload`
  - `GET /api/v1/workspaces/{id}/documents`
  - `GET /api/v1/documents/{id}`
  - `POST /api/v1/documents/{id}/reindex`
- Related schema or storage changes: `documents`, local upload storage

## Dependencies

- Prior task:
  - `phase1_db_foundation`
  - `phase1_auth_boundary`
  - `phase1_workspace_persistence`
- Blockers: none

## Scope

Allowed files:

- `server/app/api/routes/documents.py`
- `server/app/models/document.py`
- `server/app/schemas/document.py`
- `server/app/repositories/`
- `server/app/services/document_service.py`
- `server/requirements.txt`

Disallowed files:

- `web/`
- `server/app/workers/`
- `server/app/services/retrieval_service.py`

## Deliverables

- Code changes:
  - add multipart upload handling
  - save uploaded files under a stable workspace/document path
  - persist document metadata with uploader identity and status
  - replace `501 scaffold` list/get/reindex endpoints with real behavior
- Test changes:
  - add upload, list, get, and reindex API tests
- Docs changes:
  - only minimal upload/setup notes if needed

## Acceptance Criteria

- An authenticated user can upload a file into a workspace they can access
- Uploaded documents appear in workspace document lists
- Document detail returns real metadata
- Reindex is callable but does not trigger parsing or vector indexing yet
- Phase 2 ingest logic is not introduced in this task

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python -m ruff check .`
  - `..\.venv\Scripts\python -m mypy app`
  - `..\.venv\Scripts\python -m pytest`
- Frontend:
  - none

## Tests

- Normal case: upload file -> list document -> fetch detail
- Edge case: multiple uploads with the same original filename do not collide
- Error case: unknown workspace, no access, or invalid upload is rejected

## Risks

- Storing absolute file paths in the DB will make local/dev/prod portability harder than necessary

## Rollback Plan

- revert document route and persistence changes and remove any new upload-handling code
