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

### AI Hot Tracker

- Work object: high-trust current AI source material, derived themes, events, projects, and durable research records
- Primary output: frontier summaries, trend judgments, project cards, and research records
- Core capabilities: latest-source intake, AI frontier synthesis, project and event extraction, link-backed project cards
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

## Post-Phase-5 Planning Model

After the Phase 5 baseline, roadmap planning shifts from a purely phase-based build order to a three-track model:

- `Research`
- `Platform Reliability`
- `Delivery and Operations`

The first formal planning unit under that model was `Stage A`, documented in `docs/prd/STAGE_A_PLAN.md`.
`Stage B`, documented in `docs/prd/STAGE_B_PLAN.md`, is now complete and closed.
`Stage C`, documented in `docs/prd/STAGE_C_PLAN.md`, is now complete and closed.
`Stage D`, documented in `docs/prd/STAGE_D_PLAN.md`, is now complete and closed.
`Stage E`, documented in `docs/prd/STAGE_E_PLAN.md`, is now complete and closed.
`Stage F`, documented in `docs/prd/STAGE_F_PLAN.md`, is now complete and closed.
`Stage G`, documented in `docs/prd/STAGE_G_PLAN.md`, is now complete and closed.
`Stage H`, documented in `docs/prd/STAGE_H_PLAN.md`, is now complete and closed.
The most recent formal planning unit is `Stage K`, documented in `docs/prd/STAGE_K_PLAN.md`.
The longer post-Stage-C direction is tracked separately in `docs/prd/LONG_TERM_ROADMAP.md`.

## Current Status

The repository currently has the `Phase 5` baseline implemented and has completed and closed `Stage A` through
`Stage K`.

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
- one `AI 热点追踪` baseline that now runs through the shared task / agent / tool runtime and the completed MCP learning path
- structured Support Copilot and Job Assistant workflows on the same shared platform primitives
- scenario-specific eval baselines and quality summaries for research, support, and job
- cross-module workspace navigation and entry surfaces
- a frontend demo path that connects auth -> workspace -> indexed documents -> module discovery -> grounded chat -> scenario tasks -> scenario evals -> observability review
- a validated live provider path using Alibaba Cloud Model Studio's OpenAI-compatible APIs with `qwen-plus` for chat/judge flows and `text-embedding-v4` for embeddings
- first persistent non-Research workbench surfaces through Support cases and Job hiring packets
- direct case-first and hiring-packet-first continuation loops on top of the shared task runtime
- one honest public-demo rule that distinguishes fresh guided workspaces from existing workbench continuation
- a clearer first-contact user path on the home page and workspace center that separates first-time guided-demo entry
  from existing-work continuation
- one product-facing home that already behaves like a compact project start surface and now needs to become the
  canonical root route on the dedicated product host
- one denser root-home versus project-home split where the main story and actions are now more visible inside the
  first viewport
- one primary workspace workbench that now defaults to a chat-first shell, with documents and task actions behaving as
  supporting surfaces inside the same user-facing workspace
- earlier module differentiation inside that workbench through real work-object, output, and continuity guidance
- one root personal homepage and one separate project-facing route
- one conversation-first workspace where the main chat is the center, documents behave like lightweight context/upload controls, module actions behave like the next step inside the same workbench, and deeper analytics or operator detail only appears when summoned
- one product-only live host boundary where this repository now serves `weave.lmpai.online` plus
  `api.lmpai.online`, while the root homepage is deployed outside this repo behind the same shared edge
- one shared backend model-interface foundation under chat generation, embeddings, and eval judging so later capability
  waves can build on one contract instead of three separate provider call paths
- one bounded Research tool-assisted chat pilot on top of that shared model interface, visible on the main Research
  workspace surface as a mode that can show inline tool-step summaries instead of acting like ordinary grounded chat
- one bounded honesty baseline around that pilot, where recent traces surface planning and degraded-path detail and the
  backend has a regression-facing evaluation rule for visible tool steps plus honest no-source degradation
- one explicit Research background analysis run path that can persist run state beyond a single chat turn while keeping
  answer delivery, tool-step visibility, and trace linkage on the same workspace surface
- one operator-visible regression review path for recent terminal Research analysis runs, so resumed-run memory,
  degraded-path honesty, and tool-step visibility can be checked without opening raw trace JSON first
- one bounded Stage I connector foundation with a shared external-context connector contract plus one explicit
  workspace-level connector-consent API for Research workspaces
- one bounded external-context Research pilot that can combine approved external context with internal workspace
  evidence on the main Research surface while keeping the two evidence paths and degraded outcomes visibly distinct
- one operator-facing connector review baseline that can expose connector consent state, external-context use, external
  match visibility, and degraded-path honesty for recent Research analysis runs
- one explicit external-resource snapshot layer for the bounded Research connector path, so approved external matches
  can be inspected and linked back to direct chat or background analysis runs instead of living only in transient trace
  data
- one bounded local MCP server and one bounded MCP resource contract behind the existing Research consent boundary
- one visible Research MCP-backed path on the existing external-context surface
- one MCP-aware trace and operator-review baseline for that visible path
- one true out-of-process MCP client and one transport-aware MCP server contract behind that same connector boundary
- one visible Research path that now reads that bounded out-of-process MCP resource while preserving explicit consent
  and snapshot reuse
- one remote-MCP-aware trace and operator-review baseline for that same visible path
- one connector-configured true external MCP endpoint contract and one validation surface behind that same connector
- one visible Research path that now reads one true external MCP resource while preserving consent and snapshot reuse
  boundary
- one durable `ai_frontier_research_record` layer for `AI 热点追踪`
- one structured frontier-output system covering frontier summary, trend judgment, theme, event, project-card, and
  reference-source outputs
- one visible `AI 热点追踪` workbench surface that now presents durable records and structured outputs instead of the
  older broad Research framing
- one bounded trusted-source intake path for `AI 热点追踪` that now normalizes external source items before report
  generation instead of depending on one answer-first chat blob

The repository does not yet implement:

- durable or multi-agent orchestration beyond the minimal LangGraph workflow
- human approval flows, retries, or advanced scheduling
- external observability stacks, alerting, or advanced BI-style dashboards
- full production-grade hardening beyond the current bounded public-demo baseline
- the staged AI capability expansions described in `docs/prd/LONG_TERM_ROADMAP.md`

`Stage A: Research Deepening With Trust Baseline`, documented in `docs/prd/STAGE_A_PLAN.md`, is complete and closed.
`Stage B: Research Workflow Productization With Recoverable Runtime`, documented in `docs/prd/STAGE_B_PLAN.md`, is
complete and closed.
`Stage C: Multi-Module Workflow Expansion With Cross-Module Readiness`, documented in `docs/prd/STAGE_C_PLAN.md`, is
complete and closed.
`Stage D: Public Internet Demo Baseline`, documented in `docs/prd/STAGE_D_PLAN.md`, is complete and closed.
`Stage E: Support and Job Workbench Productization`, documented in `docs/prd/STAGE_E_PLAN.md`, is complete and closed.
`Stage F: Public Demo Experience Clarification and UX Reset`, documented in `docs/prd/STAGE_F_PLAN.md`, is complete and
closed.
`Stage G: Multi-Subdomain Product Split and Shared Edge Routing`, documented in `docs/prd/STAGE_G_PLAN.md`, is complete
and closed.
`Stage H: Model Interface Modernization and Tool-Visible Research Pilot`, documented in `docs/prd/STAGE_H_PLAN.md`, is
complete and closed.
`Stage K: AI Frontier Research Productization`, documented in `docs/prd/STAGE_K_PLAN.md`, is complete and closed.

Stage K started from a different question than Stage J. Stage J asked how the project could learn MCP coherently
through one independent server and one full product-side path. Stage K asked how that completed MCP baseline should
actually serve one concrete module. The answer is `AI 热点追踪`: a workflow that starts from current high-trust AI
source material, derives themes, events, and projects from that inflow, and produces summaries, judgments, project
cards, and durable research records instead of behaving like generic broad Research chat.

Stage H is now complete. The bounded Research-first capability path now includes explicit background analysis runs,
compact resumed-run memory, and one operator-visible replay/regression baseline before the roadmap opens connector or
multi-agent work. Stage I is now active, and its first wave is now complete: one bounded connector contract, one
explicit workspace-level consent boundary, one visible external-context Research pilot, and one connector-aware review
baseline now exist on the product surface. The first two tasks in the second Stage I wave are now complete: approved
external-context matches can be persisted as explicit Research external-resource snapshots, and the Research path can
now expose consent lifecycle plus explicit snapshot selection on that same bounded connector flow. The third task in
that second Stage I wave is now also complete: recent terminal Research connector runs can now be reviewed with
resource-aware visibility into selected snapshots, actual used snapshots, resource-selection mode, and consent-
lifecycle consistency. Control-plane interpretation is now explicit: `Stage I` is the bounded execution unit for the
current connector/context-plane baseline, while `docs/prd/LONG_TERM_ROADMAP.md` still describes the broader Wave 2
concept family. The current repo baseline already satisfies the minimum Wave 2 exit signal through one connector-backed
Research integration with explicit permission boundaries, but it still does not claim full MCP host, client, or server
coverage. The third Stage I wave is now complete: the repo has one bounded local MCP server, one MCP resource
contract wired to the existing Research connector consent boundary, one visible Research MCP resource-context pilot on
the existing Research surface, and one MCP-aware trace and review layer around that path. The first task in the
fourth Stage I wave is now also complete: the repo has one true out-of-process MCP client and one transport-aware MCP
server contract behind that same connector boundary. The first two tasks in the fourth Stage I wave are now also
complete: the visible Research path now reads that bounded out-of-process MCP resource while preserving explicit
consent and snapshot reuse. The fourth Stage I wave is now fully complete: remote-MCP transport, read status, denial,
transport failure, and degraded outcomes are now readable in operator review on that same visible path. The first task
in the fifth Stage I wave is now complete as well: the repo can now describe, validate, and read one connector-
configured true external MCP endpoint, the visible Research flow now uses that same true external MCP resource instead
of the earlier repo-local fallback, and endpoint identity, credential/auth state, auth detail, and honest remote
degraded behavior are now visible in trace and operator review. Stage I is now closed. Stage J opens next, still
inside Wave 2, because the project wants one complete MCP learning path built around one independent MCP server and one
fuller product-side MCP integration rather than more narrow follow-through on the old Stage I baseline. That Stage J
contract is now fixed as one independent server plus one resource, one tool, one prompt, one stdio transport, and one
bearer-style token auth model so the next work can stay coherent. That next work now serves `AI 热点追踪`, not the
older generic Research concept.

The first execution wave under that model is now archived under `tasks/archive/stage-a/`, with
`tasks/archive/stage-a/stage-a-02-research-contracts-and-structured-results.md` and
`tasks/archive/stage-a/stage-a-03-research-report-assembly-and-surface.md` and
`tasks/archive/stage-a/stage-a-04-research-trust-and-regression-baseline.md` and
`tasks/archive/stage-a/stage-a-05-delivery-and-operations-baseline.md` completed.

The second execution wave is now archived as:

- `tasks/archive/stage-a/stage-a-07-research-iteration-workflow.md`
- `tasks/archive/stage-a/stage-a-08-research-eval-baseline.md`
- `tasks/archive/stage-a/stage-a-09-staging-delivery-path.md`

The first executable Stage B wave is now complete as:

- `tasks/archive/stage-b/stage-b-02-research-workbench-and-asset-lifecycle.md` (complete)
- `tasks/archive/stage-b/stage-b-03-recoverable-runtime-and-control-actions.md` (complete)
- `tasks/archive/stage-b/stage-b-04-staging-rehearsal-automation-and-handoff.md` (complete)

The second executable Stage B wave is now complete as:

- `tasks/archive/stage-b/stage-b-06-research-briefs-and-asset-comparison.md` (complete)
- `tasks/archive/stage-b/stage-b-07-runtime-recovery-history-and-operator-visibility.md` (complete)
- `tasks/archive/stage-b/stage-b-08-release-evidence-and-rehearsal-records.md` (complete)

The first executable Stage C wave is now complete as:

- `tasks/archive/stage-c/stage-c-02-support-copilot-grounded-case-workflow.md` (complete)
- `tasks/archive/stage-c/stage-c-03-job-assistant-structured-hiring-workflow.md` (complete)
- `tasks/archive/stage-c/stage-c-04-cross-module-quality-and-demo-readiness.md` (complete)

The second executable Stage C wave is now complete as:

- `tasks/archive/stage-c/stage-c-12-support-escalation-and-follow-up-workflow.md` (complete)
- `tasks/archive/stage-c/stage-c-13-job-shortlist-and-candidate-comparison.md` (complete)
- `tasks/archive/stage-c/stage-c-14-cross-module-eval-coverage-and-rehearsal-evidence.md` (complete)
