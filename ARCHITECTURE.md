# Architecture

Stable system boundaries only. This is the short architecture summary. The long-form reference remains
`docs/architecture/PLATFORM_ARCHITECTURE.md`.

- Last Updated: 2026-04-24

## Main Modules

- shared platform core
  - auth, workspaces, documents, chat, tasks, evals, analytics, traces
- scenario modules
  - AI hot tracker, Support Copilot, Job Assistant
- supporting runtime services
  - PostgreSQL, Redis, Chroma, LangGraph, LLM providers

## Data Flow

- documents
  - upload -> parse -> chunk -> embed -> index -> retrieve
- chat
  - workspace question -> retrieval -> grounded answer -> citations -> trace
- tasks
  - create task -> queue -> worker -> agent or tool execution -> persisted result
- evals
  - dataset -> eval run -> per-case execution -> scoring -> summaries and traces
- AI hot tracker
  - workspace -> tracking profile -> allowlisted source intake -> normalized source items -> impact-oriented fixed scoring -> conservative signal clustering -> cluster-based delta evaluation -> brief synthesis -> saved tracking run or suppressed steady-state update -> grounded follow-up

## State and Persistence

- PostgreSQL is the system of record for product and workflow state.
- PostgreSQL persists workspace state, conversations, tasks, evals, and module-specific records.
- PostgreSQL persists `research_analysis_run` for bounded background analysis execution.
- PostgreSQL persists `workspace_connector_consent` and `research_external_resource_snapshot` for the bounded external-context path.
- PostgreSQL persists `ai_frontier_research_record` for older saved hot-tracker records that still need to outlive a single answer.
- PostgreSQL persists `ai_hot_tracker_tracking_run` as the durable saved run unit for the current hot-tracker product path, including:
  - profile snapshot
  - structured report output
  - normalized source payload
  - cluster-level delta summary
  - grounded follow-up thread history
- PostgreSQL persists `ai_hot_tracker_tracking_state` as the automatic-run memory layer for:
  - last cluster snapshot
  - due-time scheduling state
  - last saved or notified run pointers
  - latest saved-brief and latest meaningful-update timestamps
  - consecutive failure count and last error
- PostgreSQL persists `ai_hot_tracker_signal_memory` as the durable event-memory layer for:
  - event fingerprint and event id
  - first-seen and last-seen timestamps
  - continuity, cooling, or replacement state
  - streak count, cooling start, and replacement linkage
  - source-family and source-item linkage
  - latest rank or priority evidence and last cluster snapshot
- Research workspaces carry a default hot-tracker `tracking_profile` inside `module_config_json`.
- Redis remains the queue boundary for async execution.
- Chroma stores retrieval vectors and metadata for grounded search.
- Files under `storage/uploads/` back uploaded document content during local runtime and should be treated as runtime state rather than repo-tracked source content.

## Key Interfaces

- Next.js frontend in `web/`
- `web/app/page.tsx`
  - owns the canonical product home and the homepage-mounted auth overlay state
- `web/app/workspaces/page.tsx`
  - owns the lightweight all-workspaces history surface
- `web/components/workspace/workspace-center-panel.tsx`
  - owns the home composition and direct module-entry surface
- `web/components/workspace/workspace-workbench-panel.tsx`
  - owns the generic non-hot-tracker workspace path
- `web/components/research/ai-hot-tracker-workspace.tsx`
  - owns the dedicated AI hot-tracker surface:
    - runtime state summary
    - consumer-facing brief rendering
    - blindspots and confidence-aware signal rendering
    - saved-run history drawer
    - bounded tracking-profile editor
    - grounded follow-up side panel
    - persisted follow-up grounding summaries
    - internal evaluation variant behind `?view=evaluation`, including machine-readable judgment findings
- FastAPI API in `server/app/api/routes/`
- `server/app/api/routes/workspaces.py`
  - owns canonical workspace creation, update, and deletion paths for all environments
- `server/app/api/routes/research_analysis_runs.py`
  - owns AI hot-tracker run creation, listing, retrieval, deletion, run-bound follow-up, runtime state lookup, run evaluation lookup, and the `/ai-hot-tracker/report` alias that now resolves onto the same canonical tracking-run response path

## Runtime Boundaries

- `server/app/services/model_interface_service.py`
  - owns the shared model-facing contract for text generation, structured JSON generation, and embeddings
- `server/app/services/ai_hot_tracker_source_service.py`
  - owns trusted-source intake, list-level feed or HTML parsing, deduplication, ordering, and partial-failure capture
- `server/app/services/ai_hot_tracker_decision_service.py`
  - owns impact-oriented fixed scoring, conservative signal clustering, cluster snapshots, durable event-memory projection, and change-state classification for the hot-tracker loop
- `server/app/services/ai_hot_tracker_report_service.py`
  - owns mainstream brief-style schema-bound synthesis from ranked and clustered source candidates, including signal confidence, blindspot shaping, and the clean Chinese prompt or fallback contract for the user-facing brief path
- `server/app/services/ai_hot_tracker_tracking_service.py`
  - owns the hot-tracker control loop:
    - resolve workspace and profile
    - execute source intake
    - build ranked and clustered decisions
    - refresh event memory
    - generate a brief-style report
    - compute cluster-based delta
    - persist a saved run when required
    - update tracking state on every evaluation
    - answer grounded follow-up questions
    - expose runtime state and internal evaluation reads for the selected run
    - attach bounded agent-role traces plus machine-readable judgment checks for inspection without exposing them on the consumer path
- `server/app/services/ai_hot_tracker_follow_up_service.py`
  - owns follow-up grounding to the selected tracking run, its brief output, source items, event memory, blindspots, and prior follow-up history, and persists the bounded grounding metadata with each answer
- `server/app/services/research_external_context_service.py`
  - still owns the bounded external-context path and snapshot reuse for the research module
- `server/app/services/research_analysis_run_service.py`
  - still owns bounded background analysis runs that remain separate from the hot-tracker run model
- `server/app/repositories/ai_hot_tracker_tracking_run_repository.py`
  - owns tracking-run persistence, latest-run lookup, history queries, follow-up updates, and deletion
- `server/app/repositories/ai_hot_tracker_tracking_state_repository.py`
  - owns the hot-tracker automatic-run memory layer and next-due scheduling state
- `server/app/repositories/workspace_repository.py`
  - owns workspace persistence and also clears tracking runs and tracking state when a workspace is permanently deleted
- `server/app/workers/task_worker.py`
  - remains the live ARQ worker bundle for async task execution and now also hosts the 15-minute hot-tracker sweeper entrypoint
- `server/app/api/routes/agents.py`
  - remains a scaffolded `501` surface until a broader standalone agent runtime is introduced

## External Dependencies

- PostgreSQL
- Redis
- Chroma
- OpenAI-compatible chat and embedding providers
- Docker Compose for local orchestration
- Caddy as the shared edge for host-based frontend and API routing in the multi-subdomain deployment target

## Non-Goals

- module-specific architecture forks
- a generic chatbot story for AI hot tracker
- advanced multi-agent orchestration before the single-agent tracking loop is stronger
- exposing ranking, clustering, or delta debug details as the normal consumer-facing hot-tracker story
- reopening public-demo bootstrap behavior in deployed or local entry paths
- flattening the UI so report, history, follow-up, tasks, and analytics all compete as equal first-stop surfaces

## Change Guardrails

Human confirmation is required before:

- renaming the three module products
- replacing the shared platform-core model with module-specific silos
- changing worker, storage, or evaluation boundaries in a way that invalidates the long-form architecture docs
