# Task: phase2_retrieval_backed_chat

## Goal

Replace the Phase 1 stub chat path with retrieval-backed grounded answers and real source citations.

## Project Phase

- Phase: `Phase 2`
- Scenario module: `shared platform core`

## Why

Phase 2 is only complete when chat uses indexed workspace knowledge instead of a placeholder answer generator.

## Context

Relevant specs:

- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`

Current state:

- chat persists conversations, messages, and traces
- answers are still stubbed
- `sources` is always empty

Implementation defaults for this task:

- retrieve from Chroma using workspace-scoped filters
- keep the existing chat request and response shape stable
- fill `sources` with real document and chunk references plus minimally displayable citation data:
  - `document_id`
  - `chunk_id`
  - `document_title`
  - `chunk_index`
  - `snippet`
- record prompt/response trace data and token usage where available
- do not introduce agent planning or tool calling

## Flow Alignment

- Flow B: retrieve relevant chunks -> build prompt -> LLM answer -> save citations and trace
- Related APIs:
  - `POST /api/v1/workspaces/{id}/chat`
- Related schema or storage changes:
  - `traces`
  - source citation data in chat responses

## Dependencies

- Prior task:
  - `phase2_embeddings_and_chroma_indexing`
  - `phase2_ingest_orchestration_and_reindex`
- Blockers:
  - a configured LLM provider and embedding-backed retrieval path

## Scope

Allowed files:

- `server/app/api/routes/chat.py`
- `server/app/schemas/chat.py`
- `server/app/services/retrieval_service.py`
- `server/app/services/trace_service.py`
- `server/app/repositories/trace_repository.py`
- `server/tests/`

Disallowed files:

- `web/`
- `server/app/workers/`
- `server/app/api/routes/agents.py`
- `server/app/agents/`

## Deliverables

- Code changes:
  - replace stub retrieval with Chroma-backed retrieval
  - replace stub answer generation with LLM-backed grounded answering
  - return real `sources` entries in `ChatResponse`
  - persist trace payloads for retrieval and answer generation
- Test changes:
  - add retrieval-backed chat tests with deterministic doubles where needed
- Docs changes:
  - none required

## Acceptance Criteria

- Chat answers use indexed workspace content instead of a stub
- `sources` contains real document and chunk identifiers plus minimally displayable citation fields
- Existing conversation and trace persistence remains intact
- Tasks, agents, and evaluation flows remain out of scope

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python -m ruff check .`
  - `..\.venv\Scripts\python -m mypy app`
  - `..\.venv\Scripts\python -m pytest`
- Frontend:
  - none

## Tests

- Normal case: an indexed document yields a grounded answer with one or more sources
- Edge case: retrieval returns no relevant chunks and chat responds with a clear fallback
- Error case: LLM or retrieval failure is surfaced cleanly and trace state remains valid

## Risks

- If the source citation contract is vague now, frontend rendering and later evaluation datasets will drift

## Rollback Plan

- revert retrieval-backed chat and restore the Phase 1 stub response path while keeping persisted conversations intact
