# Task: phase2_document_parsing_and_chunking

## Goal

Implement a deterministic parsing and chunking pipeline that converts stored documents into normalized chunk records.

## Project Phase

- Phase: `Phase 2`
- Scenario module: `shared platform core`

## Why

Retrieval quality depends on clean text extraction and stable chunk boundaries; Phase 2 cannot move to embeddings or RAG without this step.

## Context

Relevant specs:

- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`

Current state:

- uploaded files are stored on disk
- there is no parsing service yet
- there is no chunking logic or `document_chunks` population

Implementation defaults for this task:

- minimum supported file types:
  - `text/plain`
  - `text/markdown`
  - `application/pdf`
- store cleaned chunk text in `document_chunks.content`
- store chunk metadata in `metadata_json`
- use deterministic chunk ordering via `chunk_index`
- keep parsing synchronous in Phase 2

## Flow Alignment

- Flow A: parse content -> chunk text -> persist chunks
- Related APIs:
  - indirectly used by `upload` and `reindex`
- Related schema or storage changes:
  - `document_chunks`
  - document status transitions through `parsing` and `chunked`

## Dependencies

- Prior task:
  - `phase2_document_schema_and_status_lifecycle`
- Blockers: none

## Scope

Allowed files:

- `server/app/services/document_service.py`
- `server/app/services/`
- `server/app/repositories/document_repository.py`
- `server/app/models/document.py`
- `server/app/models/`
- `server/requirements.txt`
- `server/tests/`

Disallowed files:

- `web/`
- `server/app/workers/`
- `server/app/api/routes/chat.py`
- `server/app/agents/`

## Deliverables

- Code changes:
  - add parser helpers for supported file types
  - add chunking logic with stable chunk size and overlap defaults
  - persist chunk rows for parsed documents
  - update document status to `parsing`, `chunked`, or `failed`
- Test changes:
  - add parsing/chunking tests for supported and unsupported files
- Docs changes:
  - none required

## Acceptance Criteria

- Supported file types can be parsed into chunk rows
- Unsupported file types fail with a clear document error state
- Chunk rows preserve deterministic ordering and metadata
- No vector indexing is performed yet in this task

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python -m ruff check .`
  - `..\.venv\Scripts\python -m mypy app`
  - `..\.venv\Scripts\python -m pytest`
- Frontend:
  - none

## Tests

- Normal case: a supported document is parsed and chunked into ordered rows
- Edge case: a very small document produces one chunk with correct metadata
- Error case: an unsupported or malformed file marks the document as `failed`

## Risks

- If chunking strategy changes later without a documented default, reindex behavior and citation stability will drift

## Rollback Plan

- revert parser/chunker changes and return documents to the pre-chunked Phase 1 metadata-only state
