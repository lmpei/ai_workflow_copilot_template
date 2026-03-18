# Architecture

Stable system boundaries only. This is the short architecture summary. The long-form reference remains
`docs/architecture/PLATFORM_ARCHITECTURE.md`.

## Metadata

- Last Updated: 2026-03-17

## Main Modules

- shared platform core
  - auth, workspaces, documents, chat, tasks, evals, analytics, traces
- scenario modules
  - Research Assistant, Support Copilot, Job Assistant
- supporting runtime services
  - PostgreSQL, Redis, Chroma, LangGraph, LLM providers

## Data Flow

- documents
  - upload -> parse -> chunk -> embed -> index -> retrieve
- chat
  - workspace question -> retrieval -> grounded answer -> citations -> trace
- tasks
  - create task -> queue -> worker -> agent/tool execution -> persisted result
- evals
  - dataset -> eval run -> per-case execution -> scoring -> summaries and traces

## State and Persistence

- PostgreSQL is the system of record for product and workflow state.
- Redis is the queue boundary for async execution.
- Chroma stores retrieval vectors and metadata for grounded search.
- Files under `storage/uploads/` back uploaded document content during local runtime.

## Key Interfaces

- Next.js frontend in `web/`
- FastAPI API in `server/app/api/routes/`
- orchestration in `server/app/services/`
- persistence in `server/app/repositories/`
- worker entrypoints in `server/app/workers/`
- agent runtime in `server/app/agents/`

## External Dependencies

- PostgreSQL
- Redis
- Chroma
- OpenAI-compatible chat and embedding providers
- Docker Compose for local orchestration

## Non-Goals

- module-specific architecture forks
- a single-purpose chatbot architecture
- advanced multi-agent durability and approval flows at the current baseline

## Change Guardrails

Human confirmation is required before:

- renaming the three module products
- replacing the shared platform-core model with module-specific silos
- changing worker, storage, or evaluation boundaries in a way that invalidates the long-form architecture docs
