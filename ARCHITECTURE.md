# Architecture

Stable system boundaries only. This is the short architecture summary. The long-form reference remains
`docs/architecture/PLATFORM_ARCHITECTURE.md`.

## Metadata

- Last Updated: 2026-03-29

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
- PostgreSQL now also persists the first non-Research workbench state through Support case / Support case event and Job
  hiring packet / Job hiring packet event records.
- Redis is the queue boundary for async execution.
- Chroma stores retrieval vectors and metadata for grounded search.
- Files under `storage/uploads/` back uploaded document content during local runtime.

## Key Interfaces

- Next.js frontend in `web/`
- `web/components/workspace/workspace-workbench-panel.tsx`
  - owns the primary workspace user path; documents, chat, and tasks now switch inside one main workbench surface
- FastAPI API in `server/app/api/routes/`
- orchestration in `server/app/services/`
- persistence in `server/app/repositories/`
- worker entrypoints in `server/app/workers/`
- agent runtime in `server/app/agents/`

## Runtime Boundaries

- `server/app/core/runtime_control.py`
  - owns cancel and retry control-state transitions plus recovery-detail derivation
- `server/app/services/task_execution_service.py`
  - owns generic task lifecycle only: pending -> running -> completed or failed
- `server/app/services/task_execution_extensions.py`
  - owns module-specific execution extensions; Research trace, lineage, and asset-sync behavior plus Support case-sync
    and Job hiring-packet sync behavior live here instead of in the generic executor
- `server/app/services/support_case_service.py`
  - owns persistent Support case synchronization, case timeline assembly, and case-action-loop guidance on top of
    completed Support task results
- `server/app/services/job_hiring_packet_service.py`
  - owns persistent Job hiring packet synchronization, hiring-timeline assembly, and packet-action-loop guidance on top of
    completed Job task results
- `server/app/repositories/support_case_repository.py`
  - owns Support case and Support case event persistence
- `server/app/repositories/job_hiring_packet_repository.py`
  - owns Job hiring packet and Job hiring packet event persistence
- `server/app/agents/graph.py`
  - owns one shared workspace-agent execution skeleton with module-specific compose steps
- `server/app/workers/task_worker.py`
  - is the only live ARQ worker bundle today
- `server/app/api/routes/agents.py`
  - remains a scaffolded `501` surface until standalone agent runtime contracts exist

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
- a flat multi-page workspace UI that treats overview, modules, documents, chat, and tasks as equal first-stop pages

## Change Guardrails

Human confirmation is required before:

- renaming the three module products
- replacing the shared platform-core model with module-specific silos
- changing worker, storage, or evaluation boundaries in a way that invalidates the long-form architecture docs
