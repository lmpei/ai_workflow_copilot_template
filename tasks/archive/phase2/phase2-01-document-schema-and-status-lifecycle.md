# Task: phase2_document_schema_and_status_lifecycle

## Goal

Add the Phase 2 persistence model for ingest and retrieval by introducing chunk, embedding-map, and richer document status data.

## Project Phase

- Phase: `Phase 2`
- Scenario module: `shared platform core`

## Why

Phase 2 needs real ingest state and chunk-level storage before parsing, indexing, or retrieval can be implemented safely.

## Context

Relevant specs:

- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`

Current state:

- `documents` metadata exists and file upload works
- no `document_chunks` storage exists yet
- no `embeddings` mapping exists yet
- document status is still Phase 1 level and does not express ingest progress clearly

Implementation defaults for this task:

- add `document_chunks` as PostgreSQL records
- add `embeddings` as vector-store mapping records, not raw vector storage
- extend document status lifecycle to at least:
  - `uploaded`
  - `parsing`
  - `chunked`
  - `indexing`
  - `indexed`
  - `failed`
- keep `document_chunks` pragmatic:
  - fixed fields for `document_id`, `chunk_index`, `content`, `token_count`, and timestamps
  - parsing-specific offsets, page numbers, and section labels go into `metadata_json`
- keep `embeddings` as mapping rows with fields such as:
  - `document_chunk_id`
  - `vector_store_id`
  - `collection_name`
  - `embedding_model`
  - timestamps

## Flow Alignment

- Flow A: upload file -> parse -> chunk -> embed -> index -> mark indexed
- Related APIs:
  - `POST /api/v1/workspaces/{id}/documents/upload`
  - `POST /api/v1/documents/{id}/reindex`
  - `GET /api/v1/workspaces/{id}/documents`
  - `GET /api/v1/documents/{id}`
- Related schema or storage changes:
  - `documents`
  - `document_chunks`
  - `embeddings`

## Dependencies

- Prior task:
  - `Phase 1 complete`
- Blockers: none

## Scope

Allowed files:

- `server/app/models/`
- `server/app/schemas/document.py`
- `server/app/repositories/document_repository.py`
- `server/app/core/`
- `server/alembic/`
- `server/tests/`

Disallowed files:

- `web/`
- `server/app/workers/`
- `server/app/agents/`

## Deliverables

- Code changes:
  - add ORM models for `document_chunks` and `embeddings`
  - extend document status handling for ingest lifecycle
  - add repository support for chunk and embedding-map persistence
  - add migration for new tables and document status changes
- Test changes:
  - add schema/repository tests for new models and status values
- Docs changes:
  - none required

## Acceptance Criteria

- The database can store chunk rows for a document
- The database can store vector-store mapping rows for a chunk
- Document status can move through the Phase 2 ingest lifecycle:
  - `uploaded -> parsing -> chunked -> indexing -> indexed`
  - failures move the document into `failed`
- Phase 1 document upload/list/get behavior remains compatible
- Async workers remain out of scope

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python -m ruff check .`
  - `..\.venv\Scripts\python -m mypy app`
  - `..\.venv\Scripts\python -m pytest`
- Frontend:
  - none

## Tests

- Normal case: create a document, chunk rows, and embedding mapping rows successfully
- Edge case: a document with zero chunks can still remain in a non-indexed state without corrupting data
- Error case: invalid status transitions or foreign-key violations are rejected cleanly

## Risks

- If status values are underspecified now, later ingest and UI work will fork into incompatible interpretations

## Rollback Plan

- revert the migration and model/repository changes; keep Phase 1 document metadata behavior intact
