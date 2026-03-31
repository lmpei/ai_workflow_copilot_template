# Architecture

Stable system boundaries only. This is the short architecture summary. The long-form reference remains
`docs/architecture/PLATFORM_ARCHITECTURE.md`.

## Metadata

- Last Updated: 2026-04-01

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
- PostgreSQL also persists the non-Research workbench state through Support case / Support case event and Job hiring
  packet / Job hiring packet event records.
- Redis is the queue boundary for async execution.
- Chroma stores retrieval vectors and metadata for grounded search.
- Files under `storage/uploads/` back uploaded document content during local runtime.

## Key Interfaces

- Next.js frontend in `web/`
- `web/app/page.tsx`
  - owns the canonical product home for the dedicated frontend host
- `web/app/app/page.tsx`
  - preserves compatibility by redirecting the older project-home route into `/`
- `web/app/workspaces/page.tsx`
  - preserves compatibility by redirecting the older workspace-center route into `/`
- `web/app/workspaces/[workspaceId]/analytics/page.tsx`
  - preserves compatibility by redirecting the older analytics page route into the workbench analytics surface
- `web/components/workspace/workspace-workbench-panel.tsx`
  - owns the primary workspace user path; the main conversation is the center of the workbench, documents behave like
    lightweight context/upload controls, module actions behave like the next step inside the same shell, and analytics,
    execution detail, or deeper document inspection belong to summoned supporting surfaces instead of equal peer
    destinations
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
  - owns persistent Job hiring packet synchronization, hiring-timeline assembly, and packet-action-loop guidance on top
    of completed Job task results
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
- Caddy as the shared edge for host-based frontend and API routing in the multi-subdomain deployment target

## Non-Goals

- module-specific architecture forks
- a single-purpose chatbot architecture
- advanced multi-agent durability and approval flows at the current baseline
- a flat or panel-balanced workspace UI that treats documents, task execution, or analytics as equal first-stop surfaces
- a deployment model where this repository still pretends to own the root marketing site instead of the dedicated
  product host

## Change Guardrails

Human confirmation is required before:

- renaming the three module products
- replacing the shared platform-core model with module-specific silos
- changing worker, storage, or evaluation boundaries in a way that invalidates the long-form architecture docs
