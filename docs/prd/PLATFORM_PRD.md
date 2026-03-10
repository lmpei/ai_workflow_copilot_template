# PRD: AI Workflow Copilot Platform

## Background

The project aims to be an AI workflow platform for knowledge work rather than a single chatbot or one-off demo.
It should support document ingestion, retrieval, agent execution, async tasks, evaluation, and observability in one
reusable platform core.

## Goal

Deliver a shared platform core that can host multiple real scenario modules on top of the same infrastructure and API
surface.

## Non-Goals

- A prompt-only demo with no persistence or workflow state
- A single-purpose tool with no reusable platform abstractions
- A pure chat UI with no document, task, or evaluation lifecycle

## Target Scenario Modules

### Job Assistant

- JD parsing
- Resume matching
- Gap analysis
- Application tracking

### Support Copilot

- Knowledge-base Q&A
- Ticket classification
- Reply drafting
- Escalation guidance

### Research Assistant

- Document retrieval
- Multi-document summarization
- Viewpoint comparison
- Report generation

## Platform Capabilities

- Workspace and project management
- Document ingest and indexing
- Retrieval and grounded chat
- Async task execution
- Agent orchestration
- Evaluation and observability

## Implementation Defaults

- Frontend: Next.js App Router with TypeScript
- Backend: FastAPI with Python

## Success Criteria

- The same core APIs and data model can support job, support, and research workflows
- Retrieval, tasks, and agent runs share workspace, trace, and metrics primitives
- Each phase produces a runnable, demoable increment

## Roadmap

### Phase 0: Scaffold & Alignment

- Product, architecture, workflow, and review docs of record
- Docker, CI, verification baseline, and Windows development support
- Backend and frontend route skeletons aligned to the target platform
- Placeholder APIs for planned platform surfaces

### Phase 1: Platform MVP

- Auth boundary
- Workspace persistence
- Document API surface
- Chat contract
- Trace and metrics minimal loop

### Phase 2: Document Ingest + RAG

- Upload metadata and persistence
- Parsing, chunking, embedding
- Chroma indexing
- Source-backed chat

### Phase 3: Tasks + Agents

- Redis-backed jobs
- Task status APIs
- LangGraph agent runs
- Tool registry

### Phase 4: Evaluation + Observability

- Evaluation datasets
- Metrics and traces
- Cost and latency reporting

### Phase 5: Scenario Modules

- Job Assistant
- Support Copilot
- Research Assistant

## Current Status

The repository is currently in `Phase 1: Platform MVP`.

The current implemented MVP includes:

- register/login auth endpoints and frontend auth flow
- workspace creation and persistence
- document upload and document metadata listing
- chat requests with persisted traces
- workspace metrics
- a frontend demo path that connects auth -> workspace -> documents -> chat -> metrics

The repository does not yet implement:

- real retrieval-backed RAG answers
- Redis-backed async workers
- LangGraph agent runs
- evaluation datasets or quality review flows
- scenario-specific job, support, or research modules
