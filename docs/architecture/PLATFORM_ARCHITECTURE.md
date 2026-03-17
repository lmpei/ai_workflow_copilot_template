# Platform Architecture

## Purpose

This document describes the target architecture of the AI Workflow Copilot Platform.
It is the architectural north star for implementation and should not be used to describe temporary scaffold state.

## Target Architecture

```text
Users
  |
  v
Next.js App Router (TypeScript-first standard)
  |
  +-- Auth UI
  +-- Workspace UI
  +-- Documents UI
  +-- Chat UI
  +-- Tasks UI
  +-- Analytics UI
  |
  v
FastAPI REST API
  |
  +-- Core Layer
  |    +-- config
  |    +-- security
  |    +-- logging
  |    +-- database
  |
  +-- API Layer
  |    +-- auth
  |    +-- workspaces
  |    +-- documents
  |    +-- chat
  |    +-- tasks
  |    +-- agents
  |    +-- evals
  |    +-- metrics
  |
  +-- Service Layer
  |    +-- auth_service
  |    +-- document_service
  |    +-- retrieval_service
  |    +-- agent_service
  |    +-- eval_service
  |    +-- trace_service
  |
  +-- Repository Layer
  |    +-- users
  |    +-- workspaces
  |    +-- documents
  |    +-- conversations
  |    +-- tasks
  |    +-- traces
  |
  +--> PostgreSQL
  |      +-- product data
  |      +-- workflow state
  |      +-- traces and metrics
  |
  +--> Redis Queue
  |      |
  |      +--> Workers
  |            +-- task execution entrypoints
  |            +-- eval execution entrypoints
  |            |
  |            +--> long-running background workflows
  |                                  |
  |                                  +--> Chroma
  |
  +--> LangGraph Runtime
         |
         +-- planning and state transitions
         +-- tool calling
         +-- human-in-the-loop checkpoints
         +-- durable execution
         |
         +--> Tools
         +--> LLM Provider
         +--> Retrieval Service
         +--> Trace Service
```

## Architecture Principles

- Build a shared platform core before building scenario-specific modules.
- Keep FastAPI route handlers thin and place orchestration logic in services.
- Isolate persistence behind repositories so in-memory scaffolds can be replaced cleanly by PostgreSQL.
- Treat Redis workers as the execution boundary for long-running, retryable, and batch workflows.
- Treat Chroma as the retrieval backend, not as the system of record.
- Treat LangGraph as the runtime for multi-step, stateful, tool-using workflows.
- Keep traces, metrics, evaluation outputs, and cost data as first-class platform data.

## Frontend Responsibilities

- Authentication and session entry points
- Workspace and document management views
- Grounded chat experience with citations
- Task submission and status tracking
- Evaluation and observability dashboards
- Scenario-specific UI for job, support, and research modules
- Frontend pages, components, and shared helpers default to TypeScript

## Backend Responsibilities

### Core Layer

- Environment configuration
- Security primitives
- Logging and observability wiring
- Database and infrastructure boundaries

### API Layer

- Typed REST contracts
- Validation and request normalization
- Workspace-scoped routing
- Auth, tasks, agents, evals, and metrics entry points

### Service Layer

- Retrieval orchestration
- Document ingest coordination
- Agent execution orchestration
- Evaluation workflow orchestration
- Trace and metrics generation

### Repository Layer

- Data access for users, workspaces, documents, conversations, tasks, and traces
- Storage abstraction between business logic and PostgreSQL

### Worker Layer

- Runtime worker entrypoints for task execution and eval execution
- Queue-backed boundaries for future long-running and retryable workflows
- No placeholder or draft workflow files in the live worker directory

### Agent Runtime

- Goal planning
- Tool execution
- Stateful workflow transitions
- Durable run persistence
- Human approval checkpoints

## Primary Flows

### Flow A: Document Ingest and Indexing

```text
upload file
  -> create document metadata
  -> queue ingest task
  -> parse content
  -> chunk text
  -> create embeddings
  -> write vectors to Chroma
  -> mark document indexed
```

### Flow B: Workspace Retrieval and Chat

```text
user asks question
  -> load workspace context
  -> retrieve relevant chunks
  -> optional rerank
  -> build prompt
  -> LLM answer
  -> save citations and trace
```

### Flow C: Agent Task Execution

```text
user starts workflow
  -> create task
  -> start LangGraph run
  -> plan steps
  -> call tools
  -> collect outputs
  -> persist final result
  -> save execution trace
```

### Flow D: Evaluation and Observability

```text
run evaluation set
  -> execute target pipeline
  -> score answer quality
  -> record latency, tokens, cost, and quality metrics
  -> expose metrics to dashboard and review flows
```

## Platform Data Model

The target platform data model includes:

- `users`
- `workspaces`
- `workspace_members`
- `documents`
- `document_chunks`
- `embeddings`
- `conversations`
- `messages`
- `tasks`
- `agent_runs`
- `tool_calls`
- `evaluations`
- `traces`

## Phase 2 Defaults

The Phase 2 implementation should use these defaults unless a later approved task changes them:

- Document status lifecycle:
  - `uploaded`
  - `parsing`
  - `chunked`
  - `indexing`
  - `indexed`
  - `failed`
- `document_chunks` should keep a pragmatic schema:
  - fixed columns for `document_id`, `chunk_index`, `content`, `token_count`, and timestamps
  - variable parsing details such as offsets, page numbers, or section labels should live in `metadata_json`
- `embeddings` should store vector-store mapping records, not raw vectors in PostgreSQL
- Phase 2 ingest should stay synchronous and inline with upload/reindex requests
- Redis-backed background ingest remains a Phase 3 concern
- Phase 2 real-integration validation should default to Alibaba Cloud Model Studio's OpenAI-compatible APIs
- Phase 2 provider wiring should remain configurable so chat and embedding providers can be switched without changing service orchestration
- Phase 2 should use one platform chat model by default for that validation path:
  - `qwen-plus`
- Phase 2 should use one platform embedding model by default for that validation path:
  - `text-embedding-v4`
- Chat and embedding base URLs must stay configurable because Model Studio region endpoints differ
- Phase 2 should use one Chroma collection for workspace documents and rely on metadata filtering by `workspace_id`
- Chroma metadata should include at least:
  - `workspace_id`
  - `document_id`
  - `chunk_id`
  - `chunk_index`
  - `document_title`
  - `mime_type`
  - `source_type`
  - `page_number` when available
- Retrieval-backed chat citations should preserve stable ids and expose minimally displayable source data:
  - `document_id`
  - `chunk_id`
  - `document_title`
  - `chunk_index`
  - `snippet`

## Target API Surface

The platform should expose these endpoint groups:

- `auth`
- `workspaces`
- `documents`
- `chat`
- `tasks`
- `agents`
- `evals`
- `metrics`

## Target Code Structure

### Backend

```text
server/
  app/
    main.py
    core/
    api/routes/
    models/
    schemas/
    services/
    repositories/
    workers/
    agents/
```

### Frontend

```text
web/
  app/
    (auth)/
    dashboard/
    workspaces/[workspaceId]/
  components/
  lib/
```

## Scenario Modules

The shared architecture must support these reusable modules without redesigning the platform core:

### Job Assistant

- Work object: hiring materials such as job descriptions, resumes, and fit criteria
- Primary output: structured job summaries, match assessments, and next-step recommendations
- Core capabilities: structured extraction, resume matching, gap analysis, application workflow support
- Not responsible for: support-case handling, knowledge-base reply generation, broad research report synthesis

### Support Copilot

- Work object: support cases, tickets, and knowledge-base context
- Primary output: grounded case summaries, reply drafts, and escalation guidance
- Core capabilities: knowledge-base retrieval, ticket classification, reply drafting, escalation guidance
- Not responsible for: broad research synthesis, multi-document comparison across a large corpus, hiring evaluation

### Research Assistant

- Work object: workspace-scoped document sets, evidence, and open research questions
- Primary output: evidence-backed synthesis and workspace reports
- Core capabilities: multi-document retrieval, evidence-backed synthesis, viewpoint comparison, report generation
- Not responsible for: ticket triage, reply drafting, candidate-to-role matching
