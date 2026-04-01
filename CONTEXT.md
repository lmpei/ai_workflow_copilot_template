# Context

Stable project facts only. Keep this file concise and update it when the project baseline changes.

## Metadata

- Last Updated: 2026-04-01
- Maintainer: project owner plus coding agents

## Project Description

AI Workflow Copilot is a shared platform core for knowledge-work AI workflows. It combines workspaces, document ingest,
grounded chat, async tasks, agent execution, evaluation, and observability so multiple scenario modules can run on the
same primitives.

Support owns one persistent case workbench layer and one direct case-action loop: a user can continue a case from the
case itself while still going through the shared task runtime. Job owns one persistent hiring-packet workbench layer and
one direct hiring-packet action loop: a user can continue shortlist or candidate-review work from the packet itself
while still going through the shared task runtime. Research remains the reference workflow when the product needs one
clear primary path.

Stage F is complete and closed after the experience reset that produced one denser product home, one
research-workflow-oriented main workspace, and one clearer distinction between primary work and summoned supporting
surfaces. Stage G is now also complete and closed after the host-boundary split: the root personal homepage at
`https://lmpai.online` is treated as a separate deployment outside this repo, while this repo now runs as the dedicated
product frontend at `https://weave.lmpai.online` plus the dedicated backend API at
`https://api.lmpai.online/api/v1` behind one shared Cloudflare -> Caddy edge.

The active work is now Stage H. Stage H opens the first bounded post-split AI-capability wave: modernize the model
interface, keep Research as the reference workflow, pilot one visible tool-assisted path, and make tool behavior
honest in traces and eval surfaces before any broader capability expansion begins.

The first Stage H foundation is now in place: one shared backend model-interface layer sits underneath chat
generation, embedding generation, and eval judging, so later capability work can build on one contract instead of on
three separate provider call paths.

The first bounded Stage H pilot is now also in place: Research workspaces can switch from ordinary grounded chat to one
tool-assisted analysis mode that plans a bounded analysis focus, uses the existing workspace tools inline, and returns
both the answer and visible tool-step summaries on the same product surface.

That first pilot now also has an honest review baseline: recent Research tool-assisted traces surface the planning
focus, search query, visible tool steps, and degraded-path reason, while the backend has one bounded regression
evaluator for tool-step visibility and honest no-source degradation.

## Current Phase

- Phase baseline: Phase 5 implemented
- Current stage: Stage A complete, Stage B complete, Stage C complete, Stage D complete, Stage E complete, Stage F
  complete, Stage G complete, and Stage H active

## Success Criteria

The platform is useful when the same core APIs and runtime can support research, support, and job workflows without
forking the architecture. The active stage should preserve that shared-platform model while beginning the next modern
AI-system layer in a bounded way: one clearer model interface, one visible tool-assisted workflow, and one honest trace
and eval baseline for that workflow.

## Technology Stack

- Backend: FastAPI, SQLAlchemy, PostgreSQL, ARQ
- Frontend: Next.js App Router, TypeScript
- Infrastructure: Docker Compose, Redis, Chroma, Caddy for the bounded public-demo rollout path and the new shared-edge
  multi-subdomain deployment target
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
  - closed Stage F planning document for the UX reset and research-workflow surface rebuild
- `docs/prd/STAGE_G_PLAN.md`
  - closed Stage G planning document for the product-only multi-subdomain deployment split
- `docs/prd/STAGE_H_PLAN.md`
  - active Stage H planning document for the first bounded model-interface modernization wave
- `tasks/`
  - active and archived task specs
- Stage task naming
  - active Stage H work uses `stage-h-*`
- root control-plane docs
  - `AGENTS.md`, `CONTEXT.md`, `STATUS.md`, `DECISIONS.md`, `ARCHITECTURE.md`

## Runtime Entrypoints

- Full stack local dev: `docker compose up --build`
- Legacy single-stack public demo path: `docker compose -f docker-compose.public-demo.yml --env-file <env-file> ...`
- New shared-edge subdomain path: `docker compose -f docker-compose.weave-stack.yml --env-file <env-file> ...`
- Live current public demo web: `https://app.lmpai.online`
- Live current public demo API: `https://api.lmpai.online/api/v1`
- Target product web host after Stage G cutover: `https://weave.lmpai.online`
- Target product API host after Stage G cutover: `https://api.lmpai.online/api/v1`
- Frontend local: `http://localhost:3000`
- API base local: `http://localhost:8000/api/v1`
- Health local: `http://localhost:8000/api/v1/health`

## Environment Intent

- `local`
  - Docker Compose on one machine with local `.env` and bundled `db` / `redis` / `chroma`
- `dev`
  - shared internal validation with environment-specific secrets and service URLs
- `staging`
  - release-like validation with explicit migration, smoke, rollback, release evidence, and handoff discipline
- `public-demo`
  - the older single-stack Linux VM path using one reverse proxy inside this repo
- `subdomain-product`
  - a product-only stack from this repo, intended to run behind one shared host-level Caddy edge as
    `weave.lmpai.online` plus `api.lmpai.online`
- `stage-h-capability-wave`
  - the same product-only stack, but now treated as the bounded environment where one model-interface modernization wave
    can ship without collapsing the stable public-demo boundary

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
- deployment drift between the older `app.<domain>` public-demo path and the new `weave.lmpai.online` product-only
  subdomain target
- host-boundary confusion if the root homepage and the product frontend are not separated cleanly in routing and docs
- documentation drift between current state, decisions, and archived task history

## Boundaries

- Do not treat the product as a single chatbot app.
- Do not bypass shared platform primitives for scenario-specific shortcuts.
- Do not rename the three module product names without confirmation.
- Do not replace the existing `docs/` or `tasks/archive/` systems; build on top of them.
- Do not treat this repository as the long-term home-site codebase for `lmpai.online`.
