# Context

Stable project facts only. Keep this file concise and update it when the project baseline changes.

## Metadata

- Last Updated: 2026-03-18
- Maintainer: project owner plus coding agents

## Project Description

AI Workflow Copilot is a shared platform core for knowledge-work AI workflows. It combines workspaces, document ingest,
grounded chat, async tasks, agent execution, evaluation, and observability so multiple scenario modules can run on the
same primitives.

## Current Phase

- Phase baseline: Phase 5 implemented
- Current stage: Stage A complete and Stage B first task wave complete

## Success Criteria

The platform is useful when the same core APIs and runtime can support research, support, and job workflows without
forking the architecture. The active stage should be executed through the three-track roadmap model, with Research as
the primary track and reliability plus delivery work treated as required parallel investment.

## Technology Stack

- Backend: FastAPI, SQLAlchemy, PostgreSQL, ARQ
- Frontend: Next.js App Router, TypeScript
- Infrastructure: Docker Compose, Redis, Chroma
- Tooling: pytest, mypy, ruff, Next.js lint/build

## Repository Overview

- `server/`
  - backend application, workers, agents, and tests
- `web/`
  - frontend routes, components, and client helpers
- `docs/`
  - long-form product, architecture, review, and development docs
- `docs/prd/STAGE_A_PLAN.md`
  - closed Stage A planning document
- `docs/prd/STAGE_B_PLAN.md`
  - active Stage B planning document
- `tasks/`
  - active and archived task specs
- Stage task naming
  - active Stage B work uses `stage-b-*`
- Phase 5 task history
  - archived under `tasks/archive/phase5/`
- root control-plane docs
  - `AGENTS.md`, `CONTEXT.md`, `STATUS.md`, `DECISIONS.md`, `ARCHITECTURE.md`

## Runtime Entrypoints

- Full stack: `docker compose up --build`
- Frontend: `http://localhost:3000`
- API base: `http://localhost:8000/api/v1`
- Health: `http://localhost:8000/api/v1/health`

## Environment Intent

- `local`
  - Docker Compose on one machine with local `.env` and bundled `db` / `redis` / `chroma`
- `dev`
  - shared internal validation with environment-specific secrets and service URLs
- `staging`
  - release-like validation with explicit migration, smoke, rollback, and handoff discipline

## Verification

- Backend: `cd server` then `..\\.venv\\Scripts\\python.exe -m pytest tests`
- Frontend: `npm --prefix web run verify`

## Risk Areas

- document ingest and reindex lifecycle
- retrieval quality and grounded citation behavior
- task and eval worker execution guarantees
- staging rehearsal drift between scripts, env conventions, and docs
- cross-module consistency across research, support, and job
- documentation drift between current state, decisions, and archived task history

## Boundaries

- Do not treat the product as a single chatbot app.
- Do not bypass shared platform primitives for scenario-specific shortcuts.
- Do not rename the three module product names without confirmation.
- Do not replace the existing `docs/` or `tasks/archive/` systems; build on top of them.
