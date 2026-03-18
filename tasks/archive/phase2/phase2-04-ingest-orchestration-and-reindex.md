# Task: phase2_ingest_orchestration_and_reindex

## Goal

Wire upload and reindex flows to a single ingest orchestration path that parses, chunks, embeds, and indexes documents end to end.

## Project Phase

- Phase: `Phase 2`
- Scenario module: `shared platform core`

## Why

The platform needs a usable ingest loop before retrieval-backed chat can work. Phase 2 should deliver this without jumping ahead to Redis workers.

## Context

Relevant specs:

- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`

Current state:

- upload persists files and metadata
- parsing, chunking, and indexing are still separate planned capabilities
- `reindex` is still a no-op placeholder from Phase 1

Implementation defaults for this task:

- keep ingest synchronous in request flow for Phase 2
- use one orchestration path for both initial upload and reindex
- make reindex idempotent by clearing stale chunk and vector mappings before rewriting
- reserve Redis-backed background jobs for Phase 3

## Flow Alignment

- Flow A: upload -> parse -> chunk -> embed -> index -> mark indexed
- Related APIs:
  - `POST /api/v1/workspaces/{id}/documents/upload`
  - `POST /api/v1/documents/{id}/reindex`
- Related schema or storage changes:
  - `documents`
  - `document_chunks`
  - `embeddings`

## Dependencies

- Prior task:
  - `phase2_document_parsing_and_chunking`
  - `phase2_embeddings_and_chroma_indexing`
- Blockers: none

## Scope

Allowed files:

- `server/app/api/routes/documents.py`
- `server/app/services/document_service.py`
- `server/app/repositories/document_repository.py`
- `server/app/repositories/`
- `server/tests/`

Disallowed files:

- `web/`
- `server/app/workers/`
- `server/app/api/routes/chat.py`
- `server/app/agents/`

## Deliverables

- Code changes:
  - add one ingest orchestration entry point in the service layer
  - call ingest during upload after metadata persistence
  - replace the Phase 1 `reindex` no-op with a real reindex path
  - clear stale chunk and embedding state before reindexing
- Test changes:
  - add upload-to-indexed and reindex tests
- Docs changes:
  - none required

## Acceptance Criteria

- Upload can produce an `indexed` document in one request path
- Reindex refreshes chunks and vector mappings for an existing document
- Failed ingest leaves clear failure status and error details
- No Redis queue or worker dependency is introduced yet

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python -m ruff check .`
  - `..\.venv\Scripts\python -m mypy app`
  - `..\.venv\Scripts\python -m pytest`
- Frontend:
  - none

## Tests

- Normal case: upload a supported document and reach `indexed`
- Edge case: reindex a previously indexed document and replace stale derived data
- Error case: ingest failure leaves the document in `failed` with no orphaned derived rows

## Risks

- Doing upload and reindex through different orchestration paths will create inconsistent document states

## Rollback Plan

- revert orchestration wiring and restore the Phase 1 upload/reindex behavior while keeping schema additions isolated
