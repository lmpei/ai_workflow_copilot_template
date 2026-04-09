# Long-Term Roadmap

## Purpose

This document captures the long-range direction after Stage C.

It is not the same as the next execution stage. It exists to keep the project's longer learning and productization path
visible without overloading the next bounded planning unit.

## Planning Status

- Status: active direction document
- Created At: 2026-03-26
- Current bounded stage: `docs/prd/STAGE_K_PLAN.md`
- Most recent bounded stage: `docs/prd/STAGE_J_PLAN.md`
- Current roadmap theme: `Theme 3: Staged AI Capability Expansion`
- Current roadmap wave: `Wave 2: Connector and Context Plane`
- Interpretation note: bounded stage closeout and roadmap-wave completion are related but not identical; the wave exit
  signal defines the minimum learning baseline, not exhaustive concept coverage

Current bounded-stage note:

- Stage K is a productization bridge stage
- it uses the completed Wave 2 MCP baseline to make one concrete `AI 前沿研究` module coherent before the project opens
  another broader capability wave

## Primary Intent

The project's first goal remains learning. The repository should help the owner understand as many important AI-system
concepts as possible by implementing them in one real system rather than only reading about them in isolation.

The project's second goal is demonstration. The system should become public enough that a collaborator, interviewer, or
peer can log into a real web application and inspect how those concepts appear in practice.

## Current Learning Baseline

The repository already covers an important first set of AI-system concepts:

- retrieval and grounded generation
- async task execution and eval execution
- workflow graphs
- structured scenario contracts
- traces, recovery detail, and operator inspection
- module-specific workflows on one shared runtime

The roadmap below should therefore focus less on repeating those basics and more on learning the next layers that are
currently shaping modern AI systems.

## Long-Range Principles

1. learning value should stay ahead of cosmetic product polish
2. the system should remain publicly demonstrable, not only locally runnable
3. new AI concepts should be introduced in bounded waves instead of as disconnected one-off features
4. eval, trace, and honest degraded-output behavior should grow with every major capability wave
5. the repository should keep one shared platform core rather than splitting into unrelated module silos

## Roadmap Themes

### Theme 1: Public Demo Baseline

The immediate long-range priority is to move from a mostly local or staging-oriented project into a real public demo.

This means:

- a public internet entrypoint
- real login and bounded user access
- sample workspaces or seeded content
- a stable showcase path through the existing module surfaces
- basic abuse, quota, and operator guardrails

This theme has now been materially delivered through the bounded Stage D, Stage F, and Stage G sequence.

### Theme 2: Non-Research Workbench Productization

After the public demo baseline is stable, the next major product depth should shift from isolated task results toward
module-specific persistent work objects.

Expected direction:

- Support Copilot:
  - case workbench
  - owner and escalation state
  - follow-up timeline
  - reusable case packet
- Job Assistant:
  - hiring packet or shortlist workbench
  - candidate-set state
  - comparison history
  - reusable interview or decision notes

This theme has now been materially delivered as a first bounded baseline through Stage E.

This theme should treat Research as the reference workflow, but it should not copy the Research asset layer blindly.

### Theme 3: Staged AI Capability Expansion

The project should keep absorbing newer AI concepts, but only through staged roadmap waves.

This theme should follow the current official direction around:

- Responses-style model interfaces and built-in tools
- MCP and connector patterns
- agent handoffs and orchestration SDKs
- reproducible agent evals and trace grading
- realtime multimodal interaction
- computer-use and action-taking agents

The goal is not to chase trends as isolated features. The goal is to use one repository to understand how those ideas
fit together in a real system.

#### Capability Planning Rules

Every AI capability wave should answer four questions before implementation starts:

1. which concept family is being learned
2. which layer of this repository changes
3. what public-demo value it adds
4. what eval, trace, safety, or approval work must ship with it

The repository should not open a capability wave unless the prerequisite product and operator layers are already stable
enough to absorb it.

#### Wave 1: Model Interface and Built-In Tool Foundation

Primary concepts:

- Responses-style model interface
- structured outputs and tool calls
- built-in web search, file search, and retrieval-oriented tool usage
- conversation state, background execution, and async result handling
- prompt caching and context compaction

Why this wave matters:

- it modernizes the model-facing interface layer without requiring a full architecture rewrite
- it clarifies how much of the platform should rely on first-party tool surfaces versus custom local pipelines

Likely repository surfaces:

- `server/app/services/`
- `server/app/agents/`
- `server/app/core/`
- eval and trace surfaces that need to expose tool behavior honestly

Learning questions:

- when should the system use first-party tools versus internal retrieval and task logic
- how should tool calls stay observable, replayable, and cost-aware
- which module flows benefit from background execution rather than synchronous request paths

Exit signal:

- at least one module uses the modern model/tool interface in a way that is visible through traces, evals, and honest
  public-demo behavior

This wave is now materially delivered as a bounded baseline through `docs/prd/STAGE_H_PLAN.md`.

#### Wave 2: Connector and Context Plane

Primary concepts:

- MCP host, client, and server roles
- MCP resources, prompts, and tools
- connector auth, consent, and permission boundaries
- external context planes beyond the repository's own database and vector store

Why this wave matters:

- it moves the platform from an internal-data workflow system toward a real context-integration host
- it teaches how to expose external systems safely instead of only calling internal tools

Likely repository surfaces:

- shared tool registry
- connector or integration layer
- workspace-level permission and consent UX
- module-specific tool availability rules

Learning questions:

- when should external capabilities appear as tools versus resources versus prompts
- where should user consent and permission review live
- how should external connector failures appear in traces, evals, and degraded outputs

Exit signal:

- one bounded MCP-backed or connector-backed integration is publicly demonstrable with explicit permission boundaries

Current Wave 2 baseline:

- `Stage I` now materially satisfies the minimum exit signal through one connector-backed Research integration with
  explicit permission boundaries
- one bounded local MCP server and one MCP-backed Research path now exist as a learning baseline
- one true out-of-process MCP client and transport foundation now exists as a delivered bounded follow-through
- the visible Research path now also reads that bounded out-of-process MCP transport
- remote-MCP transport, read status, denial, and transport failure are now explicit on that same visible path
- one connector-configured true external MCP endpoint contract and validation path now exist as the next bounded follow-through
- the visible Research path now also reads one true external MCP resource instead of the earlier repo-local subprocess fallback
- one explicit credential/auth boundary and one final review baseline now also exist around that same true external endpoint

Current Wave 2 learning gap:

- one independent MCP server outside this repository
- one product-visible MCP tool path in addition to the current resource path
- one explicit Stage J capability contract now exists so the next MCP work can implement a coherent resource, tool,
  prompt, auth, and transport learning path instead of another chain of narrow follow-through tasks
- one concrete Stage J domain now exists as well: `AI 前沿研究`, focused on current AI frontier change, industry
  evolution, and open-source ecosystem tracking
- one explicit learning baseline that covers resources, tools, prompts, auth, transport, and review together instead of across many narrow bounded follow-through tasks

#### Wave 3: Agent Orchestration and Human Approval

Primary concepts:

- specialized-agent handoffs
- planner and worker splits
- streaming partial results
- background jobs for longer-running agent work
- human-in-the-loop approval boundaries
- stronger short-term memory or session continuity

Why this wave matters:

- it turns the platform from a mostly single-workflow agent host into a clearer orchestration system
- it teaches where multi-agent coordination belongs relative to persistent workflow state

Likely repository surfaces:

- `server/app/agents/graph.py`
- `server/app/services/task_execution_service.py`
- later approval or operator-facing UI surfaces
- trace and recovery-detail contracts

Learning questions:

- which actions require human approval and which can remain automatic
- how should handoffs appear in traces and eval summaries
- how much memory belongs in runtime state versus persistent work objects

Exit signal:

- one multi-agent or planner-worker flow exists with visible handoff traces and at least one explicit approval boundary

#### Wave 4: Evaluation and Optimization Flywheel

Primary concepts:

- agent evals
- trace grading
- prompt optimization and graders
- dataset discipline
- workflow-level regression and replay

Why this wave matters:

- it turns AI capability growth into a measurable learning loop rather than a sequence of demos
- it aligns with the repository's existing strength in evals, traces, and degraded-output honesty

Likely repository surfaces:

- eval manager and dataset flows
- trace storage and inspection surfaces
- module quality baselines
- development and release-readiness docs

Learning questions:

- which failures come from prompts, which come from orchestration, and which come from tools or context
- what coverage is required before a new capability is treated as durable
- how should cross-module quality be compared without collapsing everything into one crude score

Exit signal:

- every major AI capability wave ships with explicit datasets, reproducible grading, and workflow-level regression rules

#### Wave 5: Realtime and Multimodal Interaction

Primary concepts:

- low-latency realtime interaction
- browser voice agents
- audio plus text plus image input and output
- WebRTC, WebSocket, or SIP-style connection models

Why this wave matters:

- it introduces a genuinely different interaction model instead of another async form workflow
- it exposes latency, interruption, and session design problems that batch text systems can avoid

Likely repository surfaces:

- frontend interaction model
- Support and possibly Job intake flows
- session and cost controls
- operator logging for realtime behavior

Learning questions:

- which scenarios truly benefit from voice or low-latency interaction
- what latency budget keeps the UX credible
- how should realtime sessions be traced, evaluated, and bounded for cost and abuse

Exit signal:

- one bounded realtime path is publicly demonstrable with clear cost, safety, and logging rules

#### Wave 6: Action-Taking Agents

Primary concepts:

- browser or computer-use loops
- sandboxed execution
- domain allowlists
- approval boundaries before external actions
- action-level trace capture

Why this wave matters:

- it is the clearest path from recommendation systems to agents that actually do work
- it forces the project to confront the security and operator implications of AI actions

Likely repository surfaces:

- tool execution harnesses
- approval UX
- trace and audit storage
- safety and operator documentation

Learning questions:

- which workflows should remain suggest-only instead of action-taking
- how should browser and computer-use runs be sandboxed
- which actions demand mandatory human approval

Exit signal:

- one constrained action-taking flow runs in an isolated environment with explicit allowlists, human checkpoints, and
  full action traces

#### Intentionally Deferred AI Themes

The roadmap should not rush into:

- unconstrained autonomous multi-agent swarms
- open-ended memory spanning every workflow by default
- connector marketplaces before one bounded connector pattern is understood
- unconstrained computer-use over authenticated or destructive flows

Those themes may eventually matter, but they should arrive only after the earlier waves are understood in one real
system.

### Theme 4: Cross-Cutting Trust Layer

As more capabilities enter the system, the repository should deepen the layer that makes those capabilities explainable
and testable.

Expected direction:

- stronger eval coverage and dataset discipline
- trace grading and replay
- regression baselines across prompts, tools, and workflows
- readiness scoreboards and operator-facing quality summaries
- clearer failure-shape documentation for grounded versus degraded outputs

This theme is not optional support work. It is part of how the project turns implementation into genuine learning.

## Likely Sequencing

The current expected sequence is:

1. public internet demo baseline
2. Support and Job workbench productization
3. staged AI capability waves, starting with the lower-risk interface and connector layers
4. deeper trust, eval, and replay loops across all modules

This order can change, but the repository should not skip directly into trend-driven AI features before the public demo
and non-Research workbench layers exist.

## Not A Stage Boundary

This document should not be used as the active execution source.

Use:

- `STATUS.md`
  - for the current objective and active task
- `docs/prd/STAGE_I_PLAN.md`
  - for the current bounded stage
- `tasks/`
  - for execution-ready work
