# Context

Stable project facts only. Keep this file concise and update it when the project baseline changes.

## Metadata

- Last Updated: 2026-04-09
- Maintainer: project owner plus coding agents

## Project Description

AI Workflow Copilot is a shared platform core for knowledge-work AI workflows. It combines workspaces, document ingest,
grounded chat, async tasks, agent execution, evaluation, and observability so multiple scenario modules can run on the
same primitives.

Support owns one persistent case workbench layer and one direct case-action loop: a user can continue a case from the
case itself while still going through the shared task runtime. Job owns one persistent hiring-packet workbench layer and
one direct hiring-packet action loop: a user can continue shortlist or candidate-review work from the packet itself
while still going through the shared task runtime. The older generic Research definition is now replaced at the product
definition layer by `AI 前沿研究`, which becomes the reference workflow when the product needs one clear primary path.

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

Stage I is now complete and closed. It moved the repo from internal-only tool use toward one connector and
context-plane pilot, kept Research as the reference workflow, and added explicit consent and degraded behavior before
broader connector work opened. The next bounded stage is Stage J, which keeps the same Wave 2 roadmap family but
changes the learning style: instead of more narrow MCP follow-through inside this repo, it should build one more
complete MCP understanding path around one independent MCP server plus one fuller product-side integration.

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

Stage I is complete and closed. The third Stage I wave is now complete: the repo has one bounded local MCP server, one MCP
resource contract, one visible Research MCP-backed path on the existing `research_external_context` surface, and one
MCP-aware trace and operator-review layer on that same path. The fourth Stage I wave is now also complete: the repo
now has one true out-of-process MCP client and transport foundation behind the same consent boundary, the visible
Research path now reads that bounded out-of-process MCP resource while still preserving snapshot reuse and honest
degraded behavior, and remote-MCP transport, read status, and transport failure now stay readable in trace and operator
review on that same visible path. The first two tasks in the fifth Stage I wave are now complete as well: the repo can
describe, validate, and read one connector-configured true external MCP endpoint, and the visible Research path now
uses that true external MCP resource instead of falling back to the earlier repo-local subprocess baseline. The
explicit credential/auth and review closeout around that same true external MCP endpoint is now also complete. The
bounded Stage I implementation gap is now closed. Stage J opens next because the project wants one complete MCP
learning path instead of more bounded follow-through on the same pilot baseline.

The first Stage J task is now complete as well: the project has one explicit MCP capability map, one explicit
boundary between the product repo and the future independent MCP server, and one fixed first capability set made of one
resource, one tool, one prompt, one stdio transport, and one bearer-token auth contract. Later Stage J work should
now implement that full shape instead of redefining MCP scope on every task.

The next two Stage J tasks are now also complete: one independent MCP server now exists outside this repository at
`D:\ai-try\weave-mcp-server`, and the visible `AI 前沿研究` path in this repository now uses MCP resource, tool, and
prompt behavior distinctly instead of treating MCP as resource-only context.

The final Stage J task is now complete as well: MCP tool identity, prompt identity, auth outcome, transport outcome,
and degraded behavior are now reviewable enough on the same `AI 前沿研究` path that the project can treat Stage J as a
closed learning stage instead of an open MCP catch-all.

Stage K is now active. It does not reopen MCP as another protocol-learning stage. Instead, it uses the completed
Stage J MCP baseline to turn the old generic Research surface into one concrete `AI 前沿研究` workbench with a narrower
object model, latest-source intake, structured outputs, and a clearer product surface.

The module focus is now also narrowed: the product no longer treats Research as a generic anything-research surface.
`AI 前沿研究` now means a workflow that starts from current high-trust AI source material, derives themes, events, and
projects from that inflow, and produces summaries, judgments, project cards, and durable research records with sources
kept separate from the main prose.

## Roadmap Alignment

- Current roadmap theme:
  - `Theme 3: Staged AI Capability Expansion`
- Current roadmap wave:
  - `Wave 2: Connector and Context Plane`
- Interpretation rule:
  - bounded stages are execution units; roadmap waves are broader concept families with minimum exit signals
- Current Stage K baseline:
  - one connector-backed Research integration with explicit consent, snapshots, and operator review is now delivered
  - one bounded local MCP server and MCP resource contract now sit behind that same Research-first permission model
  - one visible Research path can now actually read bounded out-of-process MCP-backed context through that same permission model
  - one bounded out-of-process MCP client and transport foundation now exists behind that same connector boundary
  - one MCP-aware trace and review baseline now makes MCP use, denial, degraded behavior, resource identity,
    transport choice, read status, and transport failure visible to operators
  - one connector-configured true external MCP endpoint contract and validation path now exist behind that same
    connector boundary
  - one visible Research path now reads one true external MCP resource while preserving consent and snapshot reuse
  - one explicit Stage J capability contract now fixes the first independent MCP server shape and the first resource,
    tool, prompt, transport, and auth model
  - the reference workflow is now explicitly `AI 前沿研究` rather than the older generic Research definition
- Still deferred:
  - any broader multi-module rollout on top of MCP
  - later roadmap-wave work after `AI 前沿研究` productization is coherent

## Current Phase

- Phase baseline: Phase 5 implemented
- Current stage: Stage A complete, Stage B complete, Stage C complete, Stage D complete, Stage E complete, Stage F
  complete, Stage G complete, Stage H complete, Stage I complete, Stage J complete, and Stage K active

## Success Criteria

The platform is useful when the same core APIs and runtime can support research, support, and job workflows without
forking the architecture. The active bounded stage should preserve that shared-platform model while adding one explicit
connector-backed Research path with clear consent, resource, and review boundaries, plus one actual visible
true-external-MCP follow-through on top of that baseline. Stage I already met that bounded goal. Stage J now exists to
learn MCP more completely by building one independent MCP server and one fuller product-side integration path for `AI 前沿研究`
instead of extending the older bounded pilot indefinitely. Roadmap-wave completion is a separate judgment against the exit
signals in
`docs/prd/LONG_TERM_ROADMAP.md`, not against exhaustive concept coverage.

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
  - closed Stage I planning document for the bounded connector and context-plane pilot wave
- `docs/prd/STAGE_J_PLAN.md`
  - closed Stage J planning document for the complete MCP understanding stage
- `docs/prd/STAGE_K_PLAN.md`
  - active Stage K planning document for AI Frontier Research productization
- `tasks/`
  - active and archived task specs
- Stage task naming
  - active Stage K work uses `stage-k-*`
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
  - the same product-only stack, but treated as the bounded environment where one connector and context-plane pilot
    shipped with explicit consent and degraded-path visibility
- `stage-j-complete-mcp-wave`
  - the same product-only stack, but treated as the bounded environment where one fuller MCP understanding path was
    learned through one independent MCP server plus one clearer product integration
- `stage-k-ai-frontier-productization-wave`
  - the same product-only stack, but now treated as the bounded environment where the completed MCP baseline is turned
    into one concrete `AI 前沿研究` module workflow

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
