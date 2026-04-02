# Architecture

Stable system boundaries only. This is the short architecture summary. The long-form reference remains
`docs/architecture/PLATFORM_ARCHITECTURE.md`.

- Last Updated: 2026-04-03

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
- bounded Research background analysis runs
  - create run -> queue worker job -> optional resumed-run memory -> tool-assisted synthesis -> assistant answer, tool
    steps, compact memory, and trace linkage
## State and Persistence

- PostgreSQL is the system of record for product and workflow state.
- PostgreSQL also persists the non-Research workbench state through Support case / Support case event and Job hiring
  packet / Job hiring packet event records, and now also persists bounded Research background analysis run state
  through `research_analysis_run` records.
- PostgreSQL now also persists bounded workspace-level connector consent state through
  `workspace_connector_consent` records before any external-context connector call path is enabled.
- PostgreSQL now also persists explicit bounded Research external-context matches as
  `research_external_resource_snapshot` records so approved connector-backed context can outlive one answer or trace.
- Redis is the queue boundary for async execution.
- Chroma stores retrieval vectors and metadata for grounded search.
- Files under `storage/uploads/` back uploaded document content during local runtime and should be treated as runtime
  state instead of repo-tracked source content.

## Key Interfaces

- Next.js frontend in `web/`
- `web/app/page.tsx`
  - owns the canonical product home for the dedicated frontend host
- `web/next.config.js`
  - preserves compatibility by redirecting the older `/app` project-home route into `/`
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
- `server/app/api/routes/connectors.py`
  - owns the bounded Stage I consent-check, consent-lifecycle, and connector-to-MCP binding API surface for the
    Research-first connector and MCP pilot path
- orchestration in `server/app/services/`
- persistence in `server/app/repositories/`
- worker entrypoints in `server/app/workers/`
- agent runtime in `server/app/agents/`

## Runtime Boundaries

- `server/app/core/runtime_control.py`
  - owns cancel and retry control-state transitions plus recovery-detail derivation
- `server/app/services/task_execution_service.py`
  - owns generic task lifecycle only: pending -> running -> completed or failed
- `server/app/services/model_interface_service.py`
  - owns the shared model-facing contract for text generation, structured JSON generation, embeddings, and future
    tool-call visibility behind the current OpenAI-compatible provider path
- `server/app/services/research_tool_assisted_chat_service.py`
  - owns the first bounded Stage H Research pilot: it plans one analysis focus plus search query, invokes existing
    workspace tools inline, synthesizes the grounded answer, and returns visible tool-step summaries to the main chat
    flow without creating a separate agent runtime surface
- `server/app/services/research_analysis_run_service.py`
  - owns the next bounded Stage H deepening step: create, queue, list, resume, and complete explicit Research
    background analysis runs that now support both the internal tool-assisted path and the Stage I external-context
    path while keeping run status, compact run memory, answer delivery, and trace linkage honest on the same workspace
    surface
- `server/app/services/research_analysis_review_service.py`
  - owns the bounded operator-facing review layer for terminal Research analysis runs by mapping persisted runs to
  their traces and applying the replay/regression baseline before any broader eval flywheel exists; it now also
  surfaces connector consent state, external-context use, match-count visibility, selected versus actual resource
  snapshot visibility, resource-selection mode, and degraded-path honesty for the Stage I pilot
- `server/app/services/connector_service.py`
  - owns the bounded Stage I connector definition registry, workspace-level consent boundary, explicit grant or revoke
    lifecycle, and reusable permission-gate helpers for the first external-context pilot
- `server/app/services/mcp_service.py`
  - owns the bounded Stage I MCP foundation layer that binds the existing Research connector to one local MCP server
    plus one MCP resource contract, and reuses the same workspace-level consent gate before any later MCP-backed
    product path is allowed to read that resource
- `server/app/mcp/research_context_local_server.py`
  - owns one in-process local MCP server foundation for the bounded Research pilot and exposes one MCP resource shape
    that later Stage I tasks can connect to a visible product path
- `server/app/services/research_external_context_service.py`
  - owns the bounded Stage I Research pilot that checks workspace connector consent, can reuse an explicitly selected
    external-resource snapshot or query the approved external context source, keeps internal and external evidence
    visibly distinct, and degrades honestly when consent, connector availability, or useful external matches are
    missing
- `server/app/services/research_external_resource_snapshot_service.py`
  - owns the bounded Stage I snapshot layer that turns approved external matches into explicit Research resource
    snapshots and exposes recent snapshots back to the product surface
- `server/app/connectors/research_external_context_connector.py`
  - owns one bounded external-context source contract for the first Research pilot instead of broad connector sprawl
- `server/app/services/retrieval_service.py`
  - owns the branch between ordinary grounded chat, the internal `research_tool_assisted` pilot, and the new
    `research_external_context` pilot mode, and now also records the extra trace metadata needed when those pilots
    are delivered through direct chat or explicit background analysis runs
- `server/app/services/chat_evaluator_service.py`
  - owns the bounded retrieval-chat and Research pilot evaluation rules, including the new regression-facing checks for
    visible tool steps, honest degraded no-source paths, and Stage I resource-selection plus consent-lifecycle
    consistency
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
- `server/app/repositories/research_analysis_run_repository.py`
  - owns `research_analysis_run` persistence, resumed-run lookup, and run-status queries for the bounded Stage H
    background-run path, and now also persists selected external-resource snapshot linkage for Stage I Wave 2
- `server/app/repositories/workspace_connector_consent_repository.py`
  - owns `workspace_connector_consent` persistence for the bounded Stage I connector-consent foundation
- `server/app/agents/graph.py`
  - owns one shared workspace-agent execution skeleton with module-specific compose steps
- `server/app/workers/task_worker.py`
  - is the only live ARQ worker bundle today and now also runs `run_research_analysis_run` for the bounded Stage H
    background-run path
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
