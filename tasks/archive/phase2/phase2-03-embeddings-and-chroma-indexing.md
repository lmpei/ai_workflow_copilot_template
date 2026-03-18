# Task: phase2_embeddings_and_chroma_indexing

## Goal

Create the embedding and vector-indexing layer that writes document chunks into Chroma and records index mappings in PostgreSQL.

## Project Phase

- Phase: `Phase 2`
- Scenario module: `shared platform core`

## Why

Phase 2 needs a real retrieval backend. Without embeddings and Chroma indexing, chat cannot move from stub answers to grounded responses.

## Context

Relevant specs:

- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`

Current state:

- no embedding provider is wired yet
- no Chroma client or collection structure exists
- no chunk-to-vector-store mapping exists yet

Implementation defaults for this task:

- use one provider-backed embedding model for the whole platform MVP
- default embedding model target: `text-embedding-3-small`
- keep provider logic behind one service abstraction so the embedding model is configurable later
- use one shared Chroma collection for workspace documents in the MVP
- namespace vectors by workspace within Chroma metadata filters, not by per-workspace collections
- record the following fields in vector metadata:
  - `workspace_id`
  - `document_id`
  - `chunk_id`
  - `chunk_index`
  - `document_title`
  - `mime_type`
  - `source_type`
  - `page_number` when available
- keep Chroma as the retrieval backend, not the system of record

## Flow Alignment

- Flow A: create embeddings -> write vectors to Chroma -> persist mapping rows
- Related APIs:
  - indirectly used by `upload` and `reindex`
- Related schema or storage changes:
  - `embeddings`
  - Chroma collections and metadata

## Dependencies

- Prior task:
  - `phase2_document_schema_and_status_lifecycle`
  - `phase2_document_parsing_and_chunking`
- Blockers:
  - a working Chroma service in local development and Docker

## Scope

Allowed files:

- `server/app/core/`
- `server/app/services/`
- `server/app/repositories/`
- `server/app/models/`
- `server/requirements.txt`
- `server/tests/`
- `docker-compose.yml`
- `.env.example`

Disallowed files:

- `web/`
- `server/app/workers/`
- `server/app/api/routes/chat.py`
- `server/app/agents/`

## Deliverables

- Code changes:
  - add embedding provider wrapper
  - add Chroma client/config wiring
  - upsert chunk vectors into Chroma
  - persist embedding mapping rows in PostgreSQL
  - update document status from `chunked` to `indexing` / `indexed` / `failed`
- Test changes:
  - add indexing tests with provider/vector-store doubles where needed
- Docs changes:
  - update local setup notes only if Chroma config changes require it

## Acceptance Criteria

- Indexed chunks are written to Chroma with stable metadata
- Chroma uses one shared collection with `workspace_id` filtering
- The relational database stores mapping rows for indexed chunks
- Repeated indexing of the same document can replace stale mappings cleanly
- No chat behavior changes in this task

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python -m ruff check .`
  - `..\.venv\Scripts\python -m mypy app`
  - `..\.venv\Scripts\python -m pytest`
- Frontend:
  - none

## Tests

- Normal case: chunk rows are embedded and indexed into Chroma with matching mapping rows
- Edge case: reindexing the same document replaces previous vector mappings without duplicates
- Error case: embedding or Chroma write failure marks the document as `failed`

## Risks

- Weak collection or metadata design here will force a painful migration when retrieval filters are introduced

## Rollback Plan

- revert embedding and Chroma integration; preserve parsed chunks and document metadata
