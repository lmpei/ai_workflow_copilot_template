# Decisions

Append-only log. Add new entries at the bottom.

## Decision Entry

- ID: DEC-2026-03-17-001
- Date: 2026-03-17
- Status: Confirmed
- Source: Human
- Topic: document control plane
- Context: the repository had strong long-form docs and task archives but no short, current control-plane docs for state, context, and decisions
- Choice: add top-level `AGENTS.md`, `CONTEXT.md`, `STATUS.md`, `DECISIONS.md`, and `ARCHITECTURE.md`
- Why: the next development stage needs faster orientation, clearer current-state tracking, and less dependence on chat history
- Impact: top-level docs become the live control plane; `docs/` and `tasks/archive/` remain in place
- Related Task: `tasks/archive/phase5/phase5-10-document-control-plane.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-17-002
- Date: 2026-03-17
- Status: Confirmed
- Source: Human
- Topic: AI rules source
- Context: the repository used `AGENT_GUIDE.md`, but the new control-plane structure requires a standard agent-facing root document
- Choice: make `AGENTS.md` the canonical AI collaboration contract and convert `AGENT_GUIDE.md` into a compatibility pointer
- Why: `AGENTS.md` is a clearer and more standard entry point for coding agents
- Impact: future agent-facing instructions should live in `AGENTS.md`
- Related Task: `tasks/archive/phase5/phase5-10-document-control-plane.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-17-003
- Date: 2026-03-17
- Status: Confirmed
- Source: Human
- Topic: legacy docs and archives
- Context: the repository already contains meaningful PRD, architecture, and task archives that should not be thrown away
- Choice: do not replace the existing `docs/` and `tasks/archive/` systems
- Why: they already hold high-value long-term context and implementation history
- Impact: the refactor is additive and organizational, not destructive
- Related Task: `tasks/archive/phase5/phase5-10-document-control-plane.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-17-004
- Date: 2026-03-17
- Status: Confirmed
- Source: Human
- Topic: sequencing for the next development stage
- Context: the team wants to discuss the next stage in multiple rounds, fix the plan in text, then develop from that text
- Choice: finish the document-layer refactor before defining the next development-stage plan
- Why: the next-stage plan should land in a cleaner operating system for humans and agents
- Impact: documentation refactor is the current active task; new feature planning follows after it
- Related Task: `tasks/archive/phase5/phase5-10-document-control-plane.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-17-005
- Date: 2026-03-17
- Status: Confirmed
- Source: Human
- Topic: module product names
- Context: the three scenario modules have naming ambiguity, but the team does not want to rename them during this refactor
- Choice: keep `Research Assistant`, `Support Copilot`, and `Job Assistant` unchanged for now
- Why: document-structure cleanup should finish before any product-name redesign work begins
- Impact: naming reconsideration is explicitly deferred to a later stage
- Related Task: `tasks/archive/phase5/phase5-10-document-control-plane.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-18-001
- Date: 2026-03-18
- Status: Confirmed
- Source: Human
- Topic: long-term roadmap model
- Context: the project is moving beyond single-phase feature delivery and needs a broader planning shape that covers product depth, engineering trust, and system delivery
- Choice: adopt a three-track roadmap model built around `Research`, `Platform Reliability`, and `Delivery and Operations`
- Why: future work should not optimize only for code features; it should also improve system reliability and real-world delivery capability
- Impact: roadmap design, task planning, and status updates should now consider all three tracks together, even when one track is the primary focus
- Related Task:
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-18-002
- Date: 2026-03-18
- Status: Confirmed
- Source: Human
- Topic: next formal planning unit
- Context: the post-Phase-5 roadmap now needs a named planning unit that can hold the first concrete three-track plan
- Choice: create `docs/prd/STAGE_A_PLAN.md` as the formal Stage A planning document
- Why: the Stage A plan is broader than a single task and more specific than the main platform PRD
- Impact: Stage A planning now has a durable home in `docs/prd/`, and later task stacks should derive from it
- Related Task: `tasks/archive/stage-a/stage-a-01-task-stack-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-18-003
- Date: 2026-03-18
- Status: Confirmed
- Source: Human
- Topic: Stage A task naming
- Context: the repository has phase-based task history, but Stage A starts a new planning unit after the Phase 5 baseline
- Choice: use `stage-a-*` naming for Stage A tasks
- Why: Stage A work should be clearly distinguishable from the earlier phase task system
- Impact: new Stage A execution tasks should follow `stage-a-*`, while archived phase tasks remain unchanged
- Related Task: `tasks/archive/stage-a/stage-a-01-task-stack-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-18-004
- Date: 2026-03-18
- Status: Confirmed
- Source: Human
- Topic: first Stage A task wave
- Context: Stage A has been fixed in text and now needs a first executable wave that respects the three-track model
- Choice: define the first Stage A wave as:
  - `tasks/archive/stage-a/stage-a-02-research-contracts-and-structured-results.md`
  - `tasks/archive/stage-a/stage-a-03-research-report-assembly-and-surface.md`
  - `tasks/archive/stage-a/stage-a-04-research-trust-and-regression-baseline.md`
  - `tasks/stage-a-05-delivery-and-operations-baseline.md`
- Why: the first wave should deepen Research while also advancing minimum reliability and delivery work in parallel
- Impact: Stage A execution can now begin from a concrete, ordered task set rather than from planning text alone
- Related Task: `tasks/archive/stage-a/stage-a-01-task-stack-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-18-005
- Date: 2026-03-18
- Status: Confirmed
- Source: Human
- Topic: Stage A activation and Phase 5 task archive
- Context: the first Stage A wave is now fixed, but the root `tasks/` directory still contains legacy Phase 5 task specs and the completed Stage A planning task
- Choice: archive the remaining `phase5-*` task specs under `tasks/archive/phase5/` and move `stage-a-01-task-stack-planning.md` under `tasks/archive/stage-a/`, leaving `tasks/` focused on active Stage A execution tasks
- Why: the root task directory should stay execution-ready and should not mix historical phase work with the current Stage A task stack
- Impact: Stage A execution moved into the first Research task wave while the completed `stage-a-02`, `stage-a-03`, and Phase 5 history remain preserved in archive
- Related Task: `tasks/archive/stage-a/stage-a-01-task-stack-planning.md`
- Supersedes:
