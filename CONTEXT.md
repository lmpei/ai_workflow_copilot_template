# Context

Stable project facts only. Keep this file concise and update it when the project baseline changes.

## Metadata

- Last Updated: 2026-04-03
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

Stage H is now complete and closed. It delivered the first bounded post-split AI-capability wave: one shared
model-interface layer, one visible Research-first tool-assisted path, explicit background analysis runs, bounded
resumed-run memory, and one operator-facing replay/regression baseline around that path.

The first Stage H foundation is now in place: one shared backend model-interface layer sits underneath chat
generation, embedding generation, and eval judging, so later capability work can build on one contract instead of on
three separate provider call paths.

The first bounded Stage H pilot is now also in place: Research workspaces can switch from ordinary grounded chat to one
tool-assisted analysis mode that plans a bounded analysis focus, uses the existing workspace tools inline, and returns
both the answer and visible tool-step summaries on the same product surface.

That first pilot now also has an honest review baseline: recent Research tool-assisted traces surface the planning
focus, search query, visible tool steps, and degraded-path reason, while the backend has one bounded regression
evaluator for tool-step visibility and honest no-source degradation.

The first two tasks in that second Stage H wave are now complete: Research workspaces can launch one explicit background
analysis run, keep that run visible through queued, running, completed, degraded, or failed state, and write the
resulting answer, tool-step summary, and trace linkage back into the same workspace flow. That run path now also has
one bounded resumed-run memory contract: later passes in the same conversation can reuse one compact prior summary, and
that carried-forward state is visible in both the run surface and the trace-review surface.

That second Stage H wave is now complete as well: recent terminal Research analysis runs now surface one bounded
operator-facing regression review alongside the existing trace view, so replay and resumed-run honesty can be reviewed
without pretending the repo already has a full optimization flywheel.

The current bounded stage is Stage I. It moves the repo from internal-only tool use toward one connector and
context-plane pilot, keeps Research as the reference workflow, and adds explicit consent and degraded behavior before
any broader connector surface or multi-agent work begins.

The first Stage I foundation is now in place as well: the backend has one bounded external-context connector contract and one workspace-level connector consent boundary for Research workspaces.

The first bounded Stage I pilot is now also in place: Research workspaces can switch to one explicit external-context mode that reuses the existing tool-assisted analysis path, checks workspace consent first, and then either blends approved external context with internal workspace evidence or degrades honestly when consent is missing, the connector is unavailable, or no useful external matches are found.

That first Stage I wave is now complete: the operator-facing review layer can distinguish connector consent state,
connector use, external-match visibility, and degraded-path honesty for the Research external-context pilot instead of
leaving that pilot as a success-only demo.

The first task in the second Stage I wave is now complete as well: approved external-context matches on the bounded
Research path no longer live only inside answer-time trace data. They can now be persisted as explicit external
resource snapshots, linked back to the direct chat turn or background analysis run that used them, and surfaced on the
main Research and observability views without collapsing them into ordinary workspace evidence.
The second task in the second Stage I wave is now complete as well: the Research connector path can now expose
explicit consent lifecycle and explicit snapshot selection instead of relying only on hidden grant state or
auto-selected external context.
The third task in the second Stage I wave is now also complete: recent terminal Research connector runs now surface one
resource-aware review baseline that makes selected snapshots, actual used snapshots, resource-selection mode, and
consent-lifecycle consistency visible to operators instead of leaving those checks implicit in raw trace payloads.

Stage I remains active. The third Stage I wave has now moved beyond MCP contract-only groundwork: the repo now has one
real MCP-backed Research path that stays on the existing visible `research_external_context` surface, reuses the same
consent and snapshot boundaries, and can degrade honestly when MCP-backed context is denied, unavailable, or empty.

## Roadmap Alignment

- Current roadmap theme:
  - `Theme 3: Staged AI Capability Expansion`
- Current roadmap wave:
  - `Wave 2: Connector and Context Plane`
- Interpretation rule:
  - bounded stages are execution units; roadmap waves are broader concept families with minimum exit signals
- Current Stage I baseline:
  - one connector-backed Research integration with explicit consent, snapshots, and operator review is now delivered
  - one bounded local MCP server and MCP resource contract now sit behind that same Research-first permission model
  - one visible Research path can now actually read bounded MCP-backed context through that same permission model
- Still deferred:
  - MCP trace and review visibility on that visible path
  - most MCP breadth across hosts, resources, prompts, and tools
  - any broader multi-module rollout on top of MCP

## Current Phase

- Phase baseline: Phase 5 implemented
- Current stage: Stage A complete, Stage B complete, Stage C complete, Stage D complete, Stage E complete, Stage F
  complete, Stage G complete, Stage H complete, and Stage I active

## Success Criteria

The platform is useful when the same core APIs and runtime can support research, support, and job workflows without
forking the architecture. The active bounded stage should preserve that shared-platform model while adding one explicit
connector-backed Research path with clear consent, resource, and review boundaries, plus one actual visible
MCP-backed follow-through on top of that baseline. Roadmap-wave completion is a separate judgment against the exit
signals in `docs/prd/LONG_TERM_ROADMAP.md`, not against exhaustive concept coverage.

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
  - closed Stage H planning document for the first bounded model-interface modernization wave
- `docs/prd/STAGE_I_PLAN.md`
  - active Stage I planning document for the bounded connector and context-plane pilot wave
- `tasks/`
  - active and archived task specs
- Stage task naming
  - active Stage I work uses `stage-i-*`
- root control-plane docs
  - `AGENTS.md`, `CONTEXT.md`, `STATUS.md`, `DECISIONS.md`, `ARCHITECTURE.md`

## Runtime Entrypoints

- Full stack local dev: `docker compose up --build`
- Legacy single-stack public demo path: `docker compose -f docker-compose.public-demo.yml --env-file <env-file> ...`
- New shared-edge subdomain path: `docker compose -f docker-compose.weave-stack.yml --env-file <env-file> ...`
- Legacy public-demo web: `https://app.lmpai.online`
- Current product web host: `https://weave.lmpai.online`
- Current product API host: `https://api.lmpai.online/api/v1`
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
  - the bounded product-only stack where the first model-interface modernization wave shipped without collapsing the
    stable public-demo boundary
- `stage-i-connector-wave`
  - the same product-only stack, but now treated as the bounded environment where one connector and context-plane pilot
    can ship with explicit consent and degraded-path visibility

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
