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
  - `tasks/archive/stage-a/stage-a-05-delivery-and-operations-baseline.md`
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

## Decision Entry

- ID: DEC-2026-03-18-006
- Date: 2026-03-18
- Status: Confirmed
- Source: Human
- Topic: second Stage A task wave
- Context: the first Stage A wave is complete, but Stage A success criteria still require deeper Research workflow capability plus a stronger regression and staging path
- Choice: define the second Stage A wave as:
  - `tasks/stage-a-07-research-iteration-workflow.md`
  - `tasks/stage-a-08-research-eval-baseline.md`
  - `tasks/stage-a-09-staging-delivery-path.md`
- Why: this keeps Research as the primary Stage A track while explicitly pairing it with the next reliability and delivery work instead of treating those tracks as optional follow-up
- Impact: `stage-a-07` becomes the next active execution task, while `stage-a-08` and `stage-a-09` form the queued parallel follow-on work for the rest of Stage A
- Related Task: `tasks/archive/stage-a/stage-a-06-wave-two-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-18-007
- Date: 2026-03-18
- Status: Confirmed
- Source: Human
- Topic: Stage A closeout
- Context: both Stage A execution waves are complete across the Research, Platform Reliability, and Delivery and Operations tracks
- Choice: close Stage A as complete instead of adding a default third Stage A wave
- Why: the Stage A success criteria are now satisfied, and future work should move into a new planning unit rather than extending Stage A without a fresh boundary
- Impact: `STATUS.md`, the PRD docs, and task planning move forward under Stage B
- Related Task: `tasks/archive/stage-b/stage-b-01-task-stack-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-18-008
- Date: 2026-03-18
- Status: Confirmed
- Source: Human
- Topic: next formal planning unit after Stage A
- Context: the project needs a post-Stage-A planning unit that keeps Research primary while advancing runtime recovery and more operator-ready delivery
- Choice: create `docs/prd/STAGE_B_PLAN.md` for `Stage B: Research Workflow Productization With Recoverable Runtime`
- Why: the next work is broader than a single task and needs a formal planning document that bridges product workflow depth, recoverable runtime behavior, and more repeatable staging operations
- Impact: Stage B becomes the active planning document and reference point for the next task wave
- Related Task: `tasks/archive/stage-b/stage-b-01-task-stack-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-18-009
- Date: 2026-03-18
- Status: Confirmed
- Source: Human
- Topic: Stage B task naming
- Context: Stage B begins after Stage A closeout and should be clearly distinguishable from both the older phase tasks and the Stage A archive
- Choice: use `stage-b-*` naming for Stage B tasks
- Why: the repository should preserve a visible planning boundary between Stage A and Stage B execution work
- Impact: new Stage B task specs now live under `tasks/` as `stage-b-*`, while completed work archives under `tasks/archive/stage-b/`
- Related Task: `tasks/archive/stage-b/stage-b-01-task-stack-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-18-010
- Date: 2026-03-18
- Status: Confirmed
- Source: Human
- Topic: first Stage B task wave
- Context: Stage B has been fixed in text and now needs an initial executable wave that matches the three-track model
- Choice: define the first Stage B wave as:
  - `tasks/stage-b-02-research-workbench-and-asset-lifecycle.md`
  - `tasks/stage-b-03-recoverable-runtime-and-control-actions.md`
  - `tasks/stage-b-04-staging-rehearsal-automation-and-handoff.md`
- Why: this keeps Research as the primary Stage B track while pairing it with the first recovery-oriented runtime and operator-oriented staging improvements
- Impact: `stage-b-02` becomes the next active execution task and the Stage B wave now has an explicit, ordered task set
- Related Task: `tasks/archive/stage-b/stage-b-01-task-stack-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-18-011
- Date: 2026-03-18
- Status: Confirmed
- Source: Human + Implementation
- Topic: Stage B Research workbench lifecycle
- Context: Stage B needed a reusable Research workflow layer so work could persist beyond isolated task outputs while preserving task lineage and revision history
- Choice: introduce persistent `research_asset` and `research_asset_revision` primitives, expose Research asset endpoints, and connect the Research surface to a workbench flow for saving, reopening, and continuing assets
- Why: Stage B Research should behave like reusable workspace work rather than a sequence of disconnected reports
- Impact: completed Research tasks can now be promoted into reusable assets, follow-up task runs can append revisions, and the UI now exposes a Stage B workbench alongside task history
- Related Task: `tasks/archive/stage-b/stage-b-02-research-workbench-and-asset-lifecycle.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-18-012
- Date: 2026-03-18
- Status: Confirmed
- Source: Human + Implementation
- Topic: Stage B recoverable runtime controls
- Context: Stage B needed clearer operator-safe recovery semantics for long-running work so failed or interrupted tasks and eval runs could be cancelled, retried, and diagnosed without relying on ambiguous status-only behavior
- Choice: add persisted `control_json` and derived `recovery_state` fields to tasks and eval runs, expose `cancel` and `retry` control endpoints, and make task/eval executors honor cancel requests at safe execution boundaries
- Why: Stage B runtime work should be easier to understand and recover without pretending to support full checkpoint/resume behavior before that foundation exists
- Impact: task and eval responses now expose recovery intent explicitly, retry attempts are linked to their source run, and operator cancellation survives worker re-entry and execution-boundary checks
- Related Task: `tasks/archive/stage-b/stage-b-03-recoverable-runtime-and-control-actions.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-18-013
- Date: 2026-03-18
- Status: Confirmed
- Source: Human + Implementation
- Topic: Stage B staging rehearsal and handoff routine
- Context: Stage B needed a more repeatable staging rehearsal path so release-like validation could be handed off without hidden knowledge or ambiguous rollback posture.
- Choice: standardize the Stage B Windows release routine around env-file-aligned preflight, a single rehearsal helper, and a handoff note that records what changed, what was checked, and which rollback target applies.
- Why: delivery work should become more repeatable and operator-friendly without overstating production guarantees or requiring a heavy deployment stack.
- Impact: `release-check-windows.cmd` now validates `APP_ENV_FILE` alignment, `staging-rehearse-windows.cmd` can execute the full Stage B rehearsal path, and the staging docs now expect an explicit handoff artifact.
- Related Task: `tasks/archive/stage-b/stage-b-04-staging-rehearsal-automation-and-handoff.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-18-014
- Date: 2026-03-18
- Status: Confirmed
- Source: Human
- Topic: Stage B wave closeout boundary
- Context: the first Stage B wave completed across the Research, Platform Reliability, and Delivery and Operations tracks, but the broader Stage B goals were not yet satisfied
- Choice: close only the first Stage B execution wave and keep Stage B itself open
- Why: the project needs another bounded Stage B wave instead of prematurely closing the whole stage or opening a new planning unit too early
- Impact: planning continues under `docs/prd/STAGE_B_PLAN.md`, with a new task wave defined under `stage-b-*`
- Related Task: `tasks/archive/stage-b/stage-b-05-wave-two-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-18-015
- Date: 2026-03-18
- Status: Confirmed
- Source: Human
- Topic: second Stage B task wave
- Context: the first Stage B wave completed the initial workbench, runtime control, and rehearsal baselines, but the stage still needs deeper Research workflow assets, better recovery visibility, and more durable release evidence
- Choice: define the second Stage B wave as:
  - `tasks/stage-b-06-research-briefs-and-asset-comparison.md`
  - `tasks/stage-b-07-runtime-recovery-history-and-operator-visibility.md`
  - `tasks/stage-b-08-release-evidence-and-rehearsal-records.md`
- Why: this keeps Research as the primary Stage B track while explicitly pairing it with the next runtime-reliability and delivery increments instead of treating those tracks as optional follow-up
- Impact: `stage-b-06` becomes the next active execution task and Stage B gains a second explicit wave instead of drifting into ad hoc work
- Related Task: `tasks/archive/stage-b/stage-b-05-wave-two-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-21-016
- Date: 2026-03-21
- Status: Confirmed
- Source: Human + Implementation
- Topic: Stage B reusable Research briefs and asset comparison
- Context: the Stage B workbench already preserved assets and revisions, but collaborators still had to inspect raw JSON to understand intent shifts or compare related research runs over time
- Choice: derive a stable Research brief from the canonical structured input, expose it on asset and revision contracts, and add a workbench comparison path for related assets or revisions
- Why: Stage B Research should feel like a reusable workflow surface rather than a collection of saved blobs or isolated task outputs
- Impact: the Research workbench now exposes reusable brief summaries, asset/revision comparison, and clearer revision-level reuse without changing the broader platform module boundaries
- Related Task: `tasks/archive/stage-b/stage-b-06-research-briefs-and-asset-comparison.md`
- Supersedes:
