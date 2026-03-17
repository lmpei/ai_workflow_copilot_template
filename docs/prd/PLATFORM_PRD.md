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

These are reusable scenario modules on one shared platform core, not three separate platforms.

### Job Assistant

- Work object: hiring materials such as job descriptions, resumes, and fit criteria
- Primary output: structured job summaries, match assessments, and next-step recommendations
- Core capabilities: structured extraction, resume matching, gap analysis, application workflow support
- Not responsible for: support-case handling, knowledge-base reply generation, broad research report synthesis

### Support Copilot

- Work object: support cases, tickets, and knowledge-base context
- Primary output: grounded case summaries, reply drafts, and escalation guidance
- Core capabilities: knowledge-base Q&A, ticket classification, reply drafting, escalation guidance
- Not responsible for: broad research synthesis, multi-document comparison across a large corpus, hiring evaluation

### Research Assistant

- Work object: workspace-scoped document sets, evidence, and open research questions
- Primary output: evidence-backed synthesis and workspace reports
- Core capabilities: grounded retrieval, multi-document summarization, viewpoint comparison, report generation
- Not responsible for: ticket triage, reply drafting, candidate-to-role matching

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

The repository is currently in `Phase 5: Scenario Modules`.

The current implemented platform increment includes:

- register/login auth endpoints and frontend auth flow
- workspace creation and persistence
- document upload, parsing, chunking, embedding, and Chroma indexing
- reindex support through the same synchronous ingest pipeline
- retrieval-backed chat with grounded source citations and persisted traces
- workspace analytics covering request volume, latency, token usage, cost, retrieval quality, task success, and eval summaries
- Redis-backed task queueing and eval queueing with ARQ worker execution
- persisted tasks, agent runs, tool calls, eval datasets, eval runs, and eval results
- a LangGraph-powered `workspace_research_agent` and static tool registry
- a chat evaluator framework that combines rule checks with an independently configured LLM judge path
- workspace module contracts for research, support, and job
- a Research Assistant MVP that produces structured scenario results through the shared task / agent / tool runtime
- Support Copilot and Job Assistant skeletons on the same shared platform primitives
- scenario-specific eval baselines and quality summaries for research, support, and job
- cross-module workspace navigation and entry surfaces
- a frontend demo path that connects auth -> workspace -> indexed documents -> module discovery -> grounded chat -> scenario tasks -> scenario evals -> observability review
- a validated live provider path using Alibaba Cloud Model Studio's OpenAI-compatible APIs with `qwen-plus` for chat/judge flows and `text-embedding-v4` for embeddings

The repository does not yet implement:

- durable or multi-agent orchestration beyond the minimal LangGraph workflow
- human approval flows, retries, or advanced scheduling
- external observability stacks, alerting, or advanced BI-style dashboards
- deeper scenario-specific product workflows beyond the current Research MVP and Support/Job skeletons
