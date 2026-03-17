# AI Development Guide

This repository supports AI coding agents and follows the workflow in `AI_WORKFLOW.md`.

## Stack

- Frontend: Next.js App Router with a TypeScript-first standard
- Backend: FastAPI
- Database: PostgreSQL
- Cache/Queue: Redis
- Vector DB target: Chroma
- Agent runtime target: LangGraph

## Product scope

- Build the shared platform core before building scenario modules
- Shared platform core: auth, workspaces, documents, chat, tasks, metrics
- Reusable scenario modules: job, support, research
- Platform docs of record:
  - `docs/prd/PLATFORM_PRD.md`
  - `docs/architecture/PLATFORM_ARCHITECTURE.md`
  - `docs/PROJECT_GUIDE.md`
- Current repository status: `Phase 5: Scenario Modules`

## Workflow contract

1. Start from a task spec in `tasks/`
2. Check the related PRD and architecture docs before editing code
3. Keep changes scoped to the task
4. Run verification before handoff
5. Document blockers instead of silently skipping them

## Repository rules

- Use the service layer for business logic
- Keep route handlers thin
- Add or update tests for new behavior
- Prefer small, scoped changes
- Reuse existing modules before creating new abstractions
- Frontend code should default to TypeScript (`.ts` / `.tsx`) unless a scoped task explicitly says otherwise
- Do not present scaffold endpoints as product-complete features
- Do not edit environment or deployment files unless the task explicitly requires it

## Build order

1. Phase 0: Scaffold & Alignment
2. Phase 1: Platform MVP
3. Phase 2: Document ingest + RAG
4. Phase 3: Tasks + Agents
5. Phase 4: Evaluation + Observability
6. Phase 5: Scenario modules

## Code boundaries

- `server/app/core/` runtime configuration and cross-cutting concerns
- `server/app/api/routes/` typed REST entry points
- `server/app/repositories/` persistence boundary
- `server/app/services/` orchestration and business logic
- `server/app/workers/` async job entry points
- `server/app/agents/` tool and workflow runtime
- `web/app/` route-level UI
- `web/components/` reusable UI building blocks

## Windows shell notes

- Local development may run in PowerShell on Windows
- Use `Copy-Item` instead of `cp` in docs or commands meant for local setup
- If PowerShell blocks `npm`, use `npm.cmd`
- Prefer `python -m <tool>` over bare `pytest`, `ruff`, or `mypy` when documenting Windows commands

## Verification baseline

Backend:

- `ruff check .`
- `mypy app`
- `pytest`

Frontend:

- `npm run lint`
- `npm run build`

Windows PowerShell equivalents:

- `npm.cmd run lint`
- `npm.cmd run build`

If a task changes only one side of the stack, run the relevant checks at minimum.

## Output expectations for coding agents

1. List modified files
2. Explain the implementation
3. Report verification status
4. Note risks, blockers, or follow-ups
