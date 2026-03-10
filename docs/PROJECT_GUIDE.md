# Project Guide

## Purpose

This document explains the role of each major document and folder, records the current development stage, and keeps
implementation aligned with the original platform vision.

## Source of Truth

### Product and Architecture

- `docs/prd/PLATFORM_PRD.md`
  - Defines the product boundary, target modules, platform capabilities, and phase roadmap.
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
  - Defines the target system architecture and the intended responsibilities of each layer.

### Archive and Decision Records

- `docs/archive/FRONTEND_TYPESCRIPT_MIGRATION.md`
  - Records the completed feasibility assessment and migration boundary for moving the frontend scaffold to TypeScript.

### Process and Execution

- `AI_WORKFLOW.md`
  - Defines the development workflow: PRD -> architecture -> tasks -> implementation -> verification -> review.
- `AGENT_GUIDE.md`
  - Defines coding-agent behavior, build order, repository boundaries, and verification expectations.
- `tasks/TASK_TEMPLATE.md`
  - Defines how individual implementation tasks are scoped and verified.
- `prompts/CODING_AGENT_PROMPT_TEMPLATE.md`
  - Defines how a coding agent should be prompted to execute a scoped task.

### Templates and Reviews

- `docs/prd/PRD_TEMPLATE.md`
  - Template for feature-level PRDs.
- `docs/architecture/ARCHITECTURE_TEMPLATE.md`
  - Template for feature-level architecture docs.
- `docs/review/HUMAN_REVIEW_CHECKLIST.md`
  - Checklist for human review before merge.
- `.github/pull_request_template.md`
  - Pull request handoff template including spec references and verification.

### Local Development

- `README.md`
  - Entry point for project orientation, quick start, and verification.
- `docs/development/WINDOWS_SETUP.md`
  - Windows-specific setup and verification guide.
- `scripts/setup-windows.cmd`
  - Windows dependency/bootstrap helper.
- `scripts/verify-windows.cmd`
  - Windows local verification helper.

## Folder Responsibilities

### Repository Root

- `server/`
  - Backend application, API, services, workers, tests, and Python runtime config.
- `web/`
  - Frontend application, shared UI components, and frontend integration helpers.
- `docs/`
  - Product, architecture, review, and development reference docs.
- `tasks/`
  - Execution-ready task specs.
- `prompts/`
  - Templates for coding-agent prompts.
- `scripts/`
  - Local helper scripts.
- `.github/`
  - CI and PR workflow metadata.

### Backend Folders

- `server/app/core/`
  - Cross-cutting runtime concerns: config, logging, security, database boundaries.
- `server/app/api/routes/`
  - REST endpoint definitions only; route handlers should stay thin.
- `server/app/models/`
  - Domain entities and persistence-oriented data structures.
- `server/app/schemas/`
  - Request and response contracts.
- `server/app/services/`
  - Business logic and orchestration.
- `server/app/repositories/`
  - Persistence boundary between services and storage.
- `server/app/workers/`
  - Async and long-running job entry points.
- `server/app/agents/`
  - Agent runtime, tools, prompts, and orchestration logic.
- `server/tests/`
  - Backend verification and API-contract tests.

### Frontend Folders

- `web/app/`
  - Route-level UI organized by App Router structure; new frontend work should default to TypeScript.
- `web/components/`
  - Reusable UI building blocks and page sections; new frontend work should default to TypeScript.
- `web/lib/`
  - Frontend integration helpers, navigation constants, and shared client logic; new frontend work should default to TypeScript.

## Current Development Status

The repository is currently in `Phase 0: Scaffold & Alignment`.

### Phase 0 Requirements

- Product, architecture, workflow, and review docs point to the same roadmap
- Local run, local verification, and CI paths exist and are documented
- Backend and frontend folder structure reflect the target platform shape
- Placeholder APIs exist for planned platform surfaces without pretending those features are complete

### Already Established

- Development workflow and spec-driven process
- Docker-based runnable environment
- CI with lint, type check, tests, and frontend build
- Backend layer skeleton for core, routes, schemas, services, repositories, workers, and agents
- Frontend route skeleton for auth, dashboard, workspaces, documents, chat, tasks, and analytics
- Frontend scaffold migrated to TypeScript
- Minimal demo loop for health, workspaces, chat, and metrics

### Not Yet Complete

- Real authentication and session management
- PostgreSQL-backed persistence
- File upload and document storage
- Parsing, chunking, embedding, and Chroma indexing
- Redis-backed worker execution
- LangGraph durable agent execution
- Evaluation datasets, trace persistence, and analytics dashboards
- Scenario-module business logic for job, support, and research

## Alignment Rules

To stay aligned with the original project vision:

1. Do not treat the project as a single chatbot app.
2. Do not skip platform primitives in order to rush to scenario-specific UI.
3. Do not implement scenario agents before document, task, and trace primitives exist.
4. Keep product, architecture, and task specs updated when the plan changes.
5. Prefer reusable platform contracts over one-off prompt flows.

## Recommended Build Order

### Phase 0: Scaffold & Alignment

- Shared roadmap and docs of record
- Local development and verification baseline
- Backend and frontend platform skeleton
- Placeholder APIs and UI shells for planned platform surfaces

### Phase 1: Platform MVP

- Auth boundary
- Workspace persistence
- Document API surface
- Chat contract
- Trace and metrics minimal loop

### Phase 2: Document Ingest + RAG

- Upload
- Metadata persistence
- Parsing and chunking
- Embeddings and Chroma indexing
- Source-backed chat

### Phase 3: Tasks + Agents

- Redis-backed jobs
- Task lifecycle
- Tool registry
- LangGraph runs

### Phase 4: Evaluation + Observability

- Trace persistence
- Cost and latency tracking
- Quality evaluation
- Analytics dashboards

### Phase 5: Scenario Modules

- Job Assistant
- Support Copilot
- Research Assistant

## Definition of "On Track"

Development is on track when:

- New work clearly maps to the PRD phase roadmap.
- New routes, services, and UI pages reinforce the shared platform core.
- Retrieval, tasks, traces, and metrics evolve as shared primitives.
- Scenario-specific work reuses the same platform contracts instead of bypassing them.
- Frontend changes follow the TypeScript-first standard captured in the architecture and agent guide.
