# Task: phase1_chat_contract_and_trace

## Goal

Keep the existing chat API contract but back it with real conversation, message, and trace persistence.

## Project Phase

- Phase: `Phase 1`
- Scenario module: `shared platform core`

## Why

Phase 1 requires a stable chat contract and a minimal trace loop even before real RAG is implemented in Phase 2.

## Context

Relevant specs:

- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`

Current state:

- `server/app/api/routes/chat.py` already returns `ChatResponse`
- chat is still a stub and does not persist any state
- `trace_id` is currently synthetic and not backed by storage

Implementation defaults for this task:

- Keep request shape: `question`, `conversation_id?`, `mode`
- Keep response shape: `answer`, `sources`, `trace_id`
- Keep answer generation stubbed in Phase 1
- Return empty `sources` until Phase 2 retrieval exists

## Flow Alignment

- Flow B: user asks question -> save conversation state -> save trace
- Related APIs:
  - `POST /api/v1/workspaces/{id}/chat`
- Related schema or storage changes: `conversations`, `messages`, `traces`

## Dependencies

- Prior task:
  - `phase1_db_foundation`
  - `phase1_auth_boundary`
  - `phase1_workspace_persistence`
- Blockers: none

## Scope

Allowed files:

- `server/app/api/routes/chat.py`
- `server/app/schemas/chat.py`
- `server/app/models/conversation.py`
- `server/app/models/trace.py`
- `server/app/repositories/`
- `server/app/services/retrieval_service.py`
- `server/app/services/trace_service.py`

Disallowed files:

- `web/`
- `server/app/api/routes/agents.py`
- `server/app/workers/`

## Deliverables

- Code changes:
  - protect the chat endpoint with auth
  - create a conversation automatically when `conversation_id` is absent
  - validate workspace ownership and conversation membership
  - persist one user message and one assistant message per request
  - persist one `trace_type = rag` trace per request
  - return the real trace primary key as `trace_id`
- Test changes:
  - add chat persistence tests for conversation, message, and trace creation
- Docs changes:
  - none required

## Acceptance Criteria

- The existing chat wire contract remains stable
- Conversations can continue across requests using `conversation_id`
- Each chat request writes real state to the database
- Empty `sources` are returned until Phase 2 retrieval exists
- Agent execution and task orchestration remain out of scope

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python -m ruff check .`
  - `..\.venv\Scripts\python -m mypy app`
  - `..\.venv\Scripts\python -m pytest`
- Frontend:
  - none

## Tests

- Normal case: first chat request creates a new conversation, messages, and trace
- Edge case: second request reuses an existing valid `conversation_id`
- Error case: invalid or foreign `conversation_id` is rejected

## Risks

- Returning demo source references in Phase 1 will contaminate future retrieval-hit metrics and confuse the roadmap

## Rollback Plan

- revert chat persistence changes and restore the existing stateless stub behavior
