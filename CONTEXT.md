# Context

Stable project facts only. Keep this file concise and update it when the project baseline changes.

## Metadata

- Last Updated: 2026-03-31
- Maintainer: project owner plus coding agents

## Project Description

AI Workflow Copilot is a shared platform core for knowledge-work AI workflows. It combines workspaces, document ingest,
grounded chat, async tasks, agent execution, evaluation, and observability so multiple scenario modules can run on the
same primitives.

The project now has one live public demo baseline at `https://app.lmpai.online`. The active stage has shifted from
public-demo delivery and non-Research workbench productization into a user-facing experience reset. Support now has a
persistent case workbench layer and a direct case-action loop: a user can continue a case from the case itself while
still going through the shared task runtime. Job now also has a direct hiring-packet action loop: a user can continue
shortlist or candidate-review work from the packet itself while still going through the shared task runtime. The live
public demo now has one bounded entry story: new viewers should start from a fresh guided demo workspace, while
existing Support or Job work should continue from the visible case or hiring-packet workbench. The workspace itself
now opens into one main workbench where the conversation is the obvious center, documents behave like lightweight
context and upload affordances, module actions behave like the next step instead of a peer panel, and deeper analytics
or operator detail only appears when the user explicitly summons it.

Human review after the third Stage F wave and the narrow density follow-up confirmed that one more reset was still needed.
That final follow-up has now landed: the root `/` page remains the personal homepage, the project-facing home at `/app`
now behaves like a denser project start surface with login/session actions at the top, one lightweight guided-demo row,
one manual-create surface, and one bounded existing-work region, and the main workspace now reads more like a
research-workflow page than a generic explanatory chat surface. Prompt chips are clearly clickable, `开始分析` is the
primary CTA, analysis progress stays in the main column, and the right rail now behaves like a research-state panel for
status, documents, analytics, trace/readiness entry, and formal output. Stage F is now waiting on a human closeout
decision rather than another active implementation task.

## Current Phase

- Phase baseline: Phase 5 implemented
- Current stage: Stage A complete, Stage B complete, Stage C complete, Stage D complete, Stage E complete, and Stage F active pending closeout after the third wave, one narrow density follow-up, and one final project-home plus research-workflow reset follow-up

## Success Criteria

The platform is useful when the same core APIs and runtime can support research, support, and job workflows without
forking the architecture. The active stage should be executed through the three-track roadmap model, with one primary
track chosen for the stage, the other two treated as required parallel investment, and Research kept as the reference
workflow when user-facing module differences and workbench depth need to be explained more clearly.

## Technology Stack

- Backend: FastAPI, SQLAlchemy, PostgreSQL, ARQ
- Frontend: Next.js App Router, TypeScript
- Infrastructure: Docker Compose, Redis, Chroma, Caddy for the bounded public-demo rollout path
- Tooling: pytest, mypy, ruff, Next.js lint/build

## Repository Overview

- `server/`
  - backend application, workers, agents, and tests
- `web/`
  - frontend routes, components, and client helpers
- `docs/`
  - long-form product, architecture, review, and development docs
- `docs/prd/LONG_TERM_ROADMAP.md`
  - long-range multi-stage learning and capability direction after Stage C
- `docs/prd/STAGE_A_PLAN.md`
  - closed Stage A planning document
- `docs/prd/STAGE_B_PLAN.md`
  - closed Stage B planning document
- `docs/prd/STAGE_C_PLAN.md`
  - closed Stage C planning document
- `docs/prd/STAGE_D_PLAN.md`
  - closed Stage D planning document
- `docs/prd/STAGE_E_PLAN.md`
  - closed Stage E planning document
- `docs/prd/STAGE_F_PLAN.md`
  - active Stage F planning document, including the current third UX-restructure wave
- `tasks/`
  - active and archived task specs
- Stage task naming
  - active Stage F work uses `stage-f-*`
- Phase 5 task history
  - archived under `tasks/archive/phase5/`
- root control-plane docs
  - `AGENTS.md`, `CONTEXT.md`, `STATUS.md`, `DECISIONS.md`, `ARCHITECTURE.md`

## Runtime Entrypoints

- Full stack local dev: `docker compose up --build`
- Public demo deployment path: `docker compose -f docker-compose.public-demo.yml --env-file <env-file> ...`
- Live public demo web: `https://app.lmpai.online`
- Live public demo API: `https://api.lmpai.online/api/v1`
- Frontend: `http://localhost:3000`
- API base: `http://localhost:8000/api/v1`
- Health: `http://localhost:8000/api/v1/health`

## Environment Intent

- `local`
  - Docker Compose on one machine with local `.env` and bundled `db` / `redis` / `chroma`
- `dev`
  - shared internal validation with environment-specific secrets and service URLs
- `staging`
  - release-like validation with explicit migration, smoke, rollback, release evidence, and handoff discipline
- `public-demo`
  - one public Linux VM using `docker-compose.public-demo.yml`, one reverse proxy, and a git-external env file

## Verification

- Backend: `cd server` then `..\.venv\Scripts\python.exe -m pytest tests`
- Frontend: `npm --prefix web run verify`

## Risk Areas

- document ingest and reindex lifecycle
- retrieval quality and grounded citation behavior
- task and eval worker execution guarantees
- deployment drift between env templates, Compose config, reverse proxy routing, smoke scripts, and docs
- cross-module consistency across research, support, and job
- continuity expectations for persisted workbench state in the live public demo
- front-end information overload, especially when abstract explanation competes with primary actions
- summoned supporting surfaces or operator detail can still pull the workspace back toward a visible tool-console feel
- a visual system that still undersells the intended product shape on the highest-traffic pages
- documentation drift between current state, decisions, and archived task history

## Boundaries

- Do not treat the product as a single chatbot app.
- Do not bypass shared platform primitives for scenario-specific shortcuts.
- Do not rename the three module product names without confirmation.
- Do not replace the existing `docs/` or `tasks/archive/` systems; build on top of them.
