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

## Decision Entry

- ID: DEC-2026-03-21-017
- Date: 2026-03-21
- Status: Confirmed
- Source: Human + Implementation
- Topic: Stage B runtime recovery history and operator visibility
- Context: Stage B runtime controls already supported cancel and retry semantics, but operators still had to infer lineage from raw `control_json` and lacked direct UI visibility into recovery state transitions.
- Choice: expose a structured `recovery_detail` contract for tasks and eval runs, preserve ordered cancel/retry history entries, and surface that recovery lineage directly in the Research and eval operator panels.
- Why: Stage B needs clearer runtime diagnostics and control lineage without overstating unsupported checkpoint/resume guarantees.
- Impact: operators can inspect why a task or eval run is in its current recovery state, retry lineage is visible through source/target links, and the UI no longer depends on raw JSON inspection for recovery debugging.
- Related Task: `tasks/archive/stage-b/stage-b-07-runtime-recovery-history-and-operator-visibility.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-21-018
- Date: 2026-03-21
- Status: Confirmed
- Source: Human + Implementation
- Topic: Stage B release evidence and rehearsal records
- Context: Stage B already had a repeatable staging rehearsal helper and handoff note, but collaborators still lacked a more durable artifact describing what the rehearsal actually checked and which rollback target applied.
- Choice: pair the existing Stage B rehearsal path with a reusable release evidence record, a helper script that generates that record, and a documented evidence template alongside the existing handoff template.
- Why: the delivery track needs clearer operator-facing evidence without pretending to be a heavier production-operations system than the project actually has.
- Impact: Stage B rehearsals now generate both release evidence and handoff artifacts, and the delivery docs now define what should be preserved after a rehearsal.
- Related Task: `tasks/archive/stage-b/stage-b-08-release-evidence-and-rehearsal-records.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-21-019
- Date: 2026-03-21
- Status: Confirmed
- Source: Human
- Topic: Stage B closeout
- Context: both Stage B execution waves are complete across Research workflow productization, recoverable runtime, and release evidence capture
- Choice: close Stage B as complete instead of adding a default third Stage B wave
- Why: the Stage B success criteria are now satisfied, and future work should move into a new planning unit rather than extending Stage B without a fresh boundary
- Impact: `STATUS.md`, the PRD docs, and task planning move forward under Stage C
- Related Task: `tasks/archive/stage-c/stage-c-01-task-stack-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-21-020
- Date: 2026-03-21
- Status: Confirmed
- Source: Human
- Topic: next formal planning unit after Stage B
- Context: the project needs a post-Stage-B planning unit that broadens deeper workflow value beyond Research while preserving the shared runtime and delivery discipline established so far
- Choice: create `docs/prd/STAGE_C_PLAN.md` for `Stage C: Multi-Module Workflow Expansion With Cross-Module Readiness`
- Why: the next work is broader than a single task and needs a formal planning document that bridges Support depth, Job depth, and cross-module readiness
- Impact: Stage C becomes the active planning document and reference point for the next task wave
- Related Task: `tasks/archive/stage-c/stage-c-01-task-stack-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-21-021
- Date: 2026-03-21
- Status: Confirmed
- Source: Human
- Topic: Stage C task naming
- Context: Stage C begins after Stage B closeout and should be clearly distinguishable from both earlier stage tasks and the older phase archive
- Choice: use `stage-c-*` naming for Stage C tasks
- Why: the repository should preserve a visible planning boundary between Stage B and Stage C execution work
- Impact: new Stage C task specs now live under `tasks/` as `stage-c-*`, while completed work archives under `tasks/archive/stage-c/`
- Related Task: `tasks/archive/stage-c/stage-c-01-task-stack-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-21-022
- Date: 2026-03-21
- Status: Confirmed
- Source: Human
- Topic: first Stage C task wave
- Context: Stage C has been fixed in text and now needs an initial executable wave that broadens scenario depth while tightening cross-module readiness
- Choice: define the first Stage C wave as:
  - `tasks/stage-c-02-support-copilot-grounded-case-workflow.md`
  - `tasks/stage-c-03-job-assistant-structured-hiring-workflow.md`
  - `tasks/stage-c-04-cross-module-quality-and-demo-readiness.md`
- Why: this keeps Research as the reference workflow while explicitly pairing deeper Support and Job surfaces with the next shared quality and delivery increment
- Impact: `stage-c-02` becomes the next active execution task and Stage C gains an explicit first task wave instead of drifting into ad hoc work
- Related Task: `tasks/archive/stage-c/stage-c-01-task-stack-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-22-023
- Date: 2026-03-22
- Status: Confirmed
- Source: Human + Analysis
- Topic: global governance baseline initiated during Stage C early execution
- Context: Stage C early execution exposed duplicated module contracts, raw JSON coupling, eroded boundaries, and Research-biased shared execution that affect the whole repository rather than only one Stage C wave
- Choice: record the diagnosis in `docs/review/STAGE_C_GOVERNANCE_DIAGNOSIS.md` and execute the resulting global governance baseline through:
  - `tasks/stage-c-06-canonical-module-contracts-and-terminology.md`
  - `tasks/stage-c-07-scenario-registry-and-boundary-hardening.md`
  - `tasks/stage-c-08-runtime-architecture-alignment.md`
  - `tasks/stage-c-09-maintainability-annotations-and-surface-hygiene.md`
- Why: the project should not open the planning unit after Stage C while duplicated contracts, boundary erosion, and hidden cross-layer coupling remain undocumented and unowned
- Impact: the repository now treats this cleanup as a global governance baseline initiated during Stage C early execution, not as a Stage C-only feature wave
- Related Task: `tasks/archive/stage-c/stage-c-05-governance-convergence-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-22-024
- Date: 2026-03-22
- Status: Confirmed
- Source: Human + Implementation
- Topic: canonical module contracts and lifecycle terminology
- Context: the global governance baseline initiated during Stage C early execution identified duplicated module identity fields, ambiguous task status language, and frontend aliases that obscured scenario-contract drift
- Choice: make `module_type` the canonical workspace identity field across storage, API, and UI, keep request-only `type` as a deprecated compatibility alias, make `task_type` the canonical task selector term, and expose `completed` as the external success-state label even while internal persistence still stores `done`
- Why: contract consumers need one authoritative vocabulary so scenario boundaries, UI state, and future registry cleanup can converge without carrying duplicate truths
- Impact: workspace responses no longer emit `type`, task responses serialize `done` as `completed`, invalid task types fail at schema validation time, and frontend shared types now use one explicit task-status vocabulary
- Related Task: `tasks/archive/stage-c/stage-c-06-canonical-module-contracts-and-terminology.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-22-025
- Date: 2026-03-22
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-c-06 canonical module contracts and terminology
- Context: stage-c-06 was executed to turn the global governance baseline into concrete API, UI, and documentation changes rather than leaving the canonical vocabulary only in review notes
- Choice: complete `stage-c-06` and archive it under `tasks/archive/stage-c/`
- Why: the repository now has one canonical workspace identity field, one external success-state label for task APIs and UI, and explicit scenario-task type usage across the frontend shared layer
- Impact: the next governance task can move to boundary hardening instead of continuing terminology cleanup, and the control plane now records `stage-c-07` as the next active step
- Related Task: `tasks/archive/stage-c/stage-c-06-canonical-module-contracts-and-terminology.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-22-026
- Date: 2026-03-22
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-c-07 scenario registry and boundary hardening
- Context: stage-c-07 executed the next step of the global governance baseline by replacing scattered scenario metadata and task-routing lists with one backend-owned registry while also removing the repository-to-service contract leak
- Choice: make `server/app/schemas/scenario.py` the canonical scenario registry, expose it through `/api/v1/scenario-modules`, derive frontend module and eval metadata from that registry, require Support and Job to reject `goal` alias input at the module boundary, and archive `stage-c-07` under `tasks/archive/stage-c/`
- Why: module availability, labels, eval prompt fields, and input boundaries should come from one owned registry instead of drifting across backend services, repositories, and frontend navigation helpers
- Impact: shared orchestration now resolves scenario behavior from one registry source, repositories no longer depend on service-layer contract resolution, and the active governance step moves to `stage-c-08` runtime architecture alignment
- Related Task: `tasks/archive/stage-c/stage-c-07-scenario-registry-and-boundary-hardening.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-22-027
- Date: 2026-03-22
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-c-08 runtime architecture alignment
- Context: stage-c-08 executed the next global governance baseline step by aligning task and eval control semantics, extracting a shared workspace-agent graph skeleton, and moving Research-only execution behavior out of the generic task executor
- Choice: centralize cancel transition helpers in `server/app/core/runtime_control.py`, make `server/app/services/task_execution_extensions.py` the explicit home for Research task trace, lineage, and asset-sync hooks, keep `server/app/services/task_execution_service.py` focused on generic task lifecycle, and archive `stage-c-08` under `tasks/archive/stage-c/`
- Why: runtime recovery semantics and module execution boundaries should be explicit and shared before the project opens the next planning unit after Stage C
- Impact: task and eval cancel paths now use the same transition model, workspace agent graphs share one execution skeleton, Research extensions no longer sit as implicit defaults inside the generic executor, and the active governance step moves to `stage-c-09`
- Related Task: `tasks/archive/stage-c/stage-c-08-runtime-architecture-alignment.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-22-028
- Date: 2026-03-22
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-c-09 maintainability annotations and close the global governance baseline
- Context: stage-c-09 executed the final governance-baseline step by marking placeholder surfaces honestly, documenting the intended runtime boundaries, and clarifying which workers and frontend surfaces are live versus legacy or scaffolded
- Choice: archive `stage-c-09`, record the placeholder-surface rules in the control-plane docs, and treat the global governance baseline initiated during Stage C early execution as complete
- Why: the repository now has durable contract, boundary, runtime, and maintainability guidance, so the planned Stage C module-depth work can resume without carrying unresolved global governance ambiguity
- Impact: the active Stage C task returns to `stage-c-02`, the archived governance stack now covers `stage-c-06` through `stage-c-09`, and future collaborators have clearer guidance about runtime semantics and placeholder surfaces
- Related Task: `tasks/archive/stage-c/stage-c-09-maintainability-annotations-and-surface-hygiene.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-23-029
- Date: 2026-03-23
- Status: Confirmed
- Source: Human + Implementation
- Topic: repair stage-c CI build drift after the governance baseline
- Context: the Stage C codebase had passed the repo's day-to-day verification baseline, but the CI workflow in `.github/workflows/ci.yml` was stricter on backend lint and typing, which left the pipeline red after the governance and runtime-alignment work
- Choice: complete an unplanned `stage-c-10` hotfix, tighten backend typing in the runtime/scenario/research execution path, and align Ruff with live application code by excluding `alembic` and `tests` and ignoring `E501`
- Why: CI must be reliable before Stage C module-depth execution can continue, and the failing checks were mostly application-type drift plus lint noise outside the maintained backend surface
- Impact: backend `ruff`, `mypy`, and `pytest` now pass again, frontend lint/build still pass, and the planned Stage C execution task remains `stage-c-02`
- Related Task: `tasks/archive/stage-c/stage-c-10-ci-build-repair.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-25-030
- Date: 2026-03-25
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-c-02 Support Copilot grounded case workflow
- Context: the governance baseline and CI repair restored the shared platform foundation, but Support Copilot still behaved like a thin launcher and result dump instead of a clearer grounded case workflow
- Choice: deepen the Support module contract around structured case input and output, add explicit case brief, grounded findings, triage, open-question, next-step, and reply-draft result fields, upgrade the Support panel to collect and display that workflow, archive `stage-c-02`, and move the active Stage C execution task to `stage-c-03`
- Why: Stage C needs to prove that deeper workflow value now extends beyond Research without bypassing the shared runtime, registry, or operator-facing inspection surfaces
- Impact: Support runs now preserve a canonical case-workflow shape, limited-context runs stay honest about missing grounding, and the next Stage C module-depth task can focus on Job Assistant instead of leaving Support at skeleton depth
- Related Task: `tasks/archive/stage-c/stage-c-02-support-copilot-grounded-case-workflow.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-25-031
- Date: 2026-03-25
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-c-03 Job Assistant structured hiring workflow
- Context: Stage C had already proven deeper workflow value for Support, but Job Assistant still behaved like a thin role-focus launcher with shallow hiring output despite running on the same shared platform core
- Choice: deepen the Job module contract around structured hiring-review input and output, add explicit hiring brief, grounded findings, gaps, fit assessment, open-question, and next-step result fields, upgrade the Job panel to collect and display that workflow, archive `stage-c-03`, and move the active Stage C execution task to `stage-c-04`
- Why: Stage C should demonstrate that both non-Research modules can now carry structured, reviewer-readable workflows without forking the shared runtime, registry, or operator inspection surfaces
- Impact: Job runs now preserve a canonical hiring-review shape, limited-context runs stay honest about missing evidence or missing materials, and the next Stage C task can focus on cross-module quality and demo readiness instead of leaving Job at skeleton depth
- Related Task: `tasks/archive/stage-c/stage-c-03-job-assistant-structured-hiring-workflow.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-25-032
- Date: 2026-03-25
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-c-04 cross-module quality and demo readiness
- Context: Stage C had already deepened Support and Job, but the first wave still lacked one shared readiness baseline that showed how Research, Support, and Job should be checked, demonstrated, and handed off together without pretending stronger production maturity than the project actually has
- Choice: add a lightweight Stage C cross-module readiness baseline, surface registry-backed quality baseline and pass-threshold guidance in the eval and workspace module surfaces, extend the Stage B delivery docs with Stage C cross-module rehearsal rules, archive `stage-c-04`, and treat the first Stage C task wave as complete
- Why: Stage C should close its first wave with one explicit shared demo and quality path rather than leaving Support and Job depth as isolated module increments
- Impact: collaborators can now point to one lightweight readiness routine across Research, Support, and Job, and the next Stage C step can be chosen from a clearer cross-module baseline instead of ad hoc module checks
- Related Task: `tasks/archive/stage-c/stage-c-04-cross-module-quality-and-demo-readiness.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-25-033
- Date: 2026-03-25
- Status: Confirmed
- Source: Human + Planning
- Topic: define the second Stage C task wave
- Context: the first Stage C wave completed Support depth, Job depth, and a lightweight cross-module readiness baseline, but the platform still needs a bounded next wave so non-Research modules can move beyond single-run structured outputs without drifting into ad hoc follow-up work
- Choice: define the second Stage C wave as `stage-c-12`, `stage-c-13`, and `stage-c-14`, using Support escalation and follow-up workflow depth, Job shortlist and candidate comparison depth, and cross-module eval-coverage plus rehearsal-evidence durability as the next ordered stack
- Why: Stage C should keep Research as the reference workflow while moving Support and Job toward multi-step reusable workflows and strengthening cross-module quality evidence at the same time
- Impact: `stage-c-12` becomes the next active execution task, the second Stage C wave is now explicit in the control plane, and future collaborators can continue Stage C without inferring the next step from chat history
- Related Task: `tasks/archive/stage-c/stage-c-11-wave-two-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-25-034
- Date: 2026-03-25
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-c-12 Support escalation and follow-up workflow depth
- Context: `stage-c-02` gave Support a structured grounded case workflow, but the module still stopped at one isolated task result and lacked a clear path for continuing a case or handing it to a reviewer-facing escalation flow
- Choice: extend the Support contract with canonical follow-up fields `parent_task_id` and `follow_up_notes`, resolve completed Support parent-task lineage before execution, add a structured `lineage` and `escalation_packet` result shape, upgrade the Support panel with continue-case actions and escalation-packet inspection, archive `stage-c-12`, and move the active Stage C task to `stage-c-13`
- Why: the second Stage C wave should push Support beyond single-run grounded outputs into a more reusable multi-step case workflow without inventing a separate persistence layer or bypassing the shared task runtime
- Impact: collaborators can continue a completed Support case without copying raw JSON by hand, Support follow-up runs now preserve parent-case lineage and reviewer-ready escalation packets, and limited-context runs stay explicit about missing grounding in the handoff output
- Related Task: `tasks/archive/stage-c/stage-c-12-support-escalation-and-follow-up-workflow.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-26-035
- Date: 2026-03-26
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-c-13 Job shortlist and candidate-comparison workflow depth
- Context: `stage-c-03` gave Job Assistant a structured single-run hiring workflow, but the module still ended at isolated candidate or JD reviews and forced collaborators to compare completed job tasks by hand
- Choice: extend the canonical Job input with `candidate_label`, `comparison_task_ids`, and `comparison_notes`, require shortlist comparisons to reference completed single-candidate `resume_match` tasks in the same workspace, add structured `comparison_candidates` and `shortlist` result fields, upgrade the Job panel with shortlist-selection and shortlist-inspection flows, archive `stage-c-13`, and move the active Stage C task to `stage-c-14`
- Why: the second Stage C wave should prove that Job Assistant can turn grounded single-run reviews into a reusable shortlist workflow without inventing a separate persistence layer or bypassing the shared task runtime
- Impact: collaborators can now build shortlist runs from completed grounded candidate reviews, Job outputs preserve evidence-linked ranking risks and interview focus, and candidate-comparison flows stay explicit about missing materials instead of implying a final hiring decision
- Related Task: `tasks/archive/stage-c/stage-c-13-job-shortlist-and-candidate-comparison.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-26-036
- Date: 2026-03-26
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-c-14 cross-module eval coverage and rehearsal evidence durability
- Context: `stage-c-04` exposed a lightweight cross-module readiness baseline, but collaborators still had to infer which module evals existed and hand-write rehearsal evidence without one durable cross-module draft path
- Choice: extend the eval manager with visible cross-module default-task coverage states and a lightweight rehearsal-evidence draft, add `docs/development/STAGE_C_REHEARSAL_EVIDENCE_TEMPLATE.md` as the reusable evidence shape, archive `stage-c-14`, and close the second Stage C task wave
- Why: the second Stage C wave should end with one explicit way to show default eval coverage and preserve a lightweight cross-module rehearsal record without overstating production maturity
- Impact: collaborators can now inspect which module default evals are covered, template-only, missing, or blocked by missing workspaces, and can capture one cross-module rehearsal evidence draft directly from the eval surface
- Related Task: `tasks/archive/stage-c/stage-c-14-cross-module-eval-coverage-and-rehearsal-evidence.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-26-037
- Date: 2026-03-26
- Status: Confirmed
- Source: Human
- Topic: close Stage C as complete
- Context: Stage C completed both execution waves, the global governance baseline initiated during Stage C early execution, and the unplanned CI repair task, so the planning question after `stage-c-14` became whether to stretch Stage C further or open a fresh boundary
- Choice: close Stage C as complete instead of extending it to cover the public-demo baseline and later roadmap themes
- Why: the next work items are broader in direction and different in emphasis from Stage C's original multi-module workflow-expansion goal
- Impact: Stage C becomes a closed reference stage, and the next bounded planning unit can focus on the public internet demo baseline without overloading the meaning of Stage C
- Related Task: `tasks/archive/stage-d/stage-d-01-task-stack-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-26-038
- Date: 2026-03-26
- Status: Confirmed
- Source: Human
- Topic: separate the long-term roadmap from the next bounded stage
- Context: the repository needs to capture a wider post-Stage-C direction that includes public demo work, non-Research workbench productization, staged AI capability expansion, and a continued trust-and-eval flywheel, but that direction is too broad for one bounded stage plan
- Choice: create `docs/prd/LONG_TERM_ROADMAP.md` as the multi-stage direction document and keep the next stage plan narrower
- Why: the project should preserve long-range learning and capability goals without turning the next stage into an unbounded catch-all
- Impact: collaborators now have one place for longer-horizon direction and another place for the next execution-ready stage
- Related Task: `tasks/archive/stage-d/stage-d-01-task-stack-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-26-039
- Date: 2026-03-26
- Status: Confirmed
- Source: Human
- Topic: define Stage D as the next bounded planning unit
- Context: after Stage C closed, the most urgent bounded next step became moving the system from local or staging-oriented use into a real public internet demo while keeping later workbench and AI-capability themes separate in the long-term roadmap
- Choice: create `docs/prd/STAGE_D_PLAN.md` for `Stage D: Public Internet Demo Baseline`, adopt `stage-d-*` naming, and define the first Stage D wave as:
  - `tasks/stage-d-02-public-demo-foundation-and-guardrails.md`
  - `tasks/stage-d-03-demo-content-seeding-and-showcase-path.md`
  - `tasks/stage-d-04-public-demo-ops-readiness.md`
- Why: the repository needs one bounded next stage that is comparable in scope to Stages A through C instead of overloading the next planning unit with every future roadmap theme at once
- Impact: `stage-d-02` becomes the next active execution task, Stage D becomes the active planning unit, and the long-term roadmap stays separate from the immediate task stack
- Related Task: `tasks/archive/stage-d/stage-d-01-task-stack-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-26-040
- Date: 2026-03-26
- Status: Confirmed
- Source: Human
- Topic: clarify the AI capability roadmap after Stage C
- Context: the first long-term roadmap captured the correct post-Stage-C themes, but the AI capability section still grouped too many concepts together and did not show clear sequencing, repository touchpoints, or learning-completion signals
- Choice: refine `docs/prd/LONG_TERM_ROADMAP.md` so the AI capability direction is organized into explicit waves covering model interfaces and built-in tools, connector and context planes, agent orchestration and approval, evaluation and optimization, realtime multimodal interaction, and action-taking agents
- Why: the project's first goal is learning, so the roadmap should make AI capability adoption legible as a staged learning path rather than as an undifferentiated list of trendy concepts
- Impact: collaborators can now understand which AI capability families belong earlier or later, why each wave matters, and how those waves should remain separate from the bounded Stage D public-demo scope
- Related Task: `tasks/archive/stage-d/stage-d-01a-ai-capability-roadmap-clarification.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-26-041
- Date: 2026-03-26
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-d-02 public-demo foundation and guardrails
- Context: Stage D needed a bounded first execution step that would make the public-demo access path explicit before content seeding, showcase flows, or ops-ready deployment work continued
- Choice: add public-demo mode settings in backend config, expose a backend-owned `/api/v1/public-demo` settings endpoint, enforce bounded registration, workspace, document, task, and upload guardrails when public-demo mode is enabled, surface those limits in the home, auth, and workspace entry UI, archive `stage-d-02`, and move the active Stage D task to `stage-d-03`
- Why: outside users should see explicit demo limits and honest failure behavior instead of relying on hidden operator assumptions or silently discovering undefined capacity boundaries
- Impact: the repository now has one operator-visible contract for public-demo guardrails, self-serve registration can be paused cleanly, public-demo users see the current limits before creating work, and the next Stage D task can focus on seeded content and showcase-path clarity rather than basic access control
- Related Task: `tasks/archive/stage-d/stage-d-02-public-demo-foundation-and-guardrails.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-26-042
- Date: 2026-03-26
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-d-03 demo content seeding and showcase path
- Context: `stage-d-02` established the public-demo guardrail contract, but first-time users still had to start from empty workspaces and infer which documents, prompts, or module inputs would demonstrate the system honestly
- Choice: add backend-owned public-demo templates, allow authenticated creation of seeded guided-demo workspaces, seed demo-safe documents through the real ingest path, expose the templates in home and workspace entry UI, add a workspace-level guided showcase panel, document the repeatable showcase path, archive `stage-d-03`, and move the active Stage D task to `stage-d-04`
- Why: a public demo needs a repeatable first-time-user path that shows real workflow depth without hidden operator setup or fake product polish
- Impact: the repo now has one backend source of truth for public-demo templates, first-time users can reach grounded module value quickly after login, and Stage D can move on to operator restart, refresh, and rollback readiness
- Related Task: `tasks/archive/stage-d/stage-d-03-demo-content-seeding-and-showcase-path.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-26-043
- Date: 2026-03-26
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-d-04 public-demo ops readiness
- Context: after `stage-d-03`, the public demo had honest guardrails and guided showcase paths, but the operator still lacked one bounded restart, refresh, smoke, and rollback routine tailored to the public-demo baseline instead of the older Stage B staging path
- Choice: add Windows helper scripts for public-demo smoke and bounded refresh, document the public-demo operator runbook, cross-link that routine from the existing public-demo and delivery docs, archive `stage-d-04`, and leave the next Stage D direction open for human confirmation
- Why: the public demo should be operable without hidden tribal knowledge while still staying honest about its limited operational maturity
- Impact: operators now have one repo-native path for public-demo preflight, restart/refresh, smoke, and manual rollback expectations, and the first Stage D wave is complete
- Related Task: `tasks/archive/stage-d/stage-d-04-public-demo-ops-readiness.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-26-044
- Date: 2026-03-26
- Status: Confirmed
- Source: Human + Implementation
- Topic: define the second Stage D wave for real public rollout
- Context: the first Stage D wave completed the bounded public-demo baseline with guardrails, guided showcase paths, and an operator routine, but the repository still lacked the next bounded task stack that would turn that baseline into a real internet-accessible rollout path
- Choice: keep Stage D open, define the second Stage D wave as `stage-d-06`, `stage-d-07`, and `stage-d-08`, focus that wave on hosting-target selection, deployment-path wiring, and one public rollout rehearsal, archive the planning task as `stage-d-05`, and move the active Stage D task to `stage-d-06`
- Why: the next meaningful step is not more feature work; it is the bounded rollout path that makes the demo reachable through a real public URL
- Impact: the control plane now points at one execution-ready Stage D wave for real internet rollout, while the earlier public-demo baseline remains preserved as the first Stage D wave
- Related Task: `tasks/archive/stage-d/stage-d-05-wave-two-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-26-045
- Date: 2026-03-26
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-d-06 public hosting target and deployment contract
- Context: the second Stage D wave needed one explicit deployment target before repo-side wiring or rollout rehearsal could proceed, but the project priority remained speed-to-demo rather than infrastructure sophistication
- Choice: choose a single small public Linux VM running the existing Docker Compose-style stack as the first hosting target, document the public URL model as `app.<domain>` plus `api.<domain>`, fix the env, persistence, smoke, and rollback contract in `docs/development/PUBLIC_DEPLOYMENT_CONTRACT.md`, archive `stage-d-06`, and move the active Stage D task to `stage-d-07`
- Why: this is the shortest path to a real public rollout that still matches the current repository architecture honestly
- Impact: the next deployment task can now wire one bounded target instead of reasoning abstractly about many platforms at once
- Related Task: `tasks/archive/stage-d/stage-d-06-public-hosting-target-and-deployment-contract.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-26-046
- Date: 2026-03-26
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-d-07 public demo deployment path and env wiring
- Context: the hosting target for the first public rollout was fixed in `stage-d-06`, but the repo still only had local-development Compose wiring and could not honestly claim one bounded deployment path for the chosen VM target
- Choice: add `docker-compose.public-demo.yml`, public-demo deploy Dockerfiles, a Caddy reverse-proxy config, `.env.public-demo.example`, `scripts/public-demo-deploy-windows.cmd`, and related deployment docs; also align the app config with `APP_ENV` and comma-delimited `CORS_ORIGINS`, archive `stage-d-07`, and move the active Stage D task to `stage-d-08`
- Why: the public rollout rehearsal needs one concrete repo-side path before any real VM deployment can be attempted
- Impact: the repository now contains one honest first-deployment path for the public demo, while the final remaining Stage D step is to execute and record the rollout rehearsal rather than design the path abstractly
- Related Task: `tasks/archive/stage-d/stage-d-07-public-demo-deployment-path-and-env-wiring.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-27-047
- Date: 2026-03-27
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-d-08 public internet rollout and rehearsal evidence
- Context: `stage-d-07` fixed the first bounded public deployment path, but Stage D still lacked one honest live rehearsal record showing a real public URL, real smoke results, and a preserved rollback baseline
- Choice: execute the first bounded public rollout on the chosen single-VM target, verify the live public URLs `https://app.lmpai.online` and `https://api.lmpai.online/api/v1`, record the rollout evidence and handoff under `docs/development/`, archive `stage-d-08`, and leave Stage D open pending human confirmation on the next bounded direction
- Why: the public-demo baseline is not meaningfully complete until one real outside-facing rehearsal proves the system can be reached, used, and described honestly
- Impact: the repository now has one durable public rollout record, one known-good deployed revision `9c68935`, and one live demo baseline that can be refreshed or rolled back with bounded operator expectations
- Related Task: `tasks/archive/stage-d/stage-d-08-public-internet-rollout-and-operator-rehearsal.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-27-048
- Date: 2026-03-27
- Status: Confirmed
- Source: Human
- Topic: close Stage D as complete
- Context: Stage D reached its bounded goal once the first live public-demo rehearsal succeeded through `app.lmpai.online` and the repo captured rollout evidence, handoff notes, and a rollback baseline.
- Choice: close Stage D as complete instead of extending it into public-demo hardening or later workbench productization.
- Why: the Stage D goal was a real public internet demo baseline, not indefinite deployment iteration.
- Impact: the next bounded planning unit can focus on persistent Support and Job workbench depth instead of continuing to overload Stage D.
- Related Task: `tasks/archive/stage-d/stage-d-08-public-internet-rollout-and-operator-rehearsal.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-27-049
- Date: 2026-03-27
- Status: Confirmed
- Source: Human
- Topic: define Stage E as the next bounded planning unit
- Context: after Stage D closed, the next most valuable bounded step is to move Support and Job from structured task-result workflows into persistent workbench surfaces while preserving the live demo baseline.
- Choice: create `docs/prd/STAGE_E_PLAN.md` for `Stage E: Support and Job Workbench Productization` and adopt `stage-e-*` naming for Stage E tasks.
- Why: the next work is broader than a single task but narrower than the long-term roadmap, and it should not be mixed back into Stage D.
- Impact: Stage E becomes the active planning unit and the root `tasks/` directory can now hold the first Stage E execution wave.
- Related Task: `tasks/archive/stage-e/stage-e-01-task-stack-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-27-050
- Date: 2026-03-27
- Status: Confirmed
- Source: Human + Planning
- Topic: define the first Stage E task wave
- Context: Stage E needs one explicit first execution wave so Support and Job workbench depth can advance without losing public-demo continuity.
- Choice: define the first Stage E wave as `stage-e-02`, `stage-e-03`, and `stage-e-04`, with `stage-e-02` as the active task.
- Why: this keeps Stage E focused on Support case workbench depth, Job hiring workbench depth, and public-demo continuity as one bounded package.
- Impact: Stage E now has an execution-ready task stack instead of a plan with no queue.
- Related Task: `tasks/archive/stage-e/stage-e-01-task-stack-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-28-051
- Date: 2026-03-28
- Status: Confirmed
- Source: Human
- Topic: insert a bounded Stage E localization pass before workbench productization continues
- Context: Stage E has already opened its first workbench wave, but the live public demo still exposes a large amount
  of English static copy across the frontend, public-demo templates, and directly surfaced backend error messages.
- Choice: add `tasks/stage-e-05-static-surface-chinese-localization.md` as a bounded active task that converts the
  live demo's user-visible static surface to Chinese while keeping module product names, model outputs, and runtime
  contracts unchanged.
- Why: the public demo should present a coherent Chinese-first experience before deeper Support and Job workbench work
  continues, but that polish pass is smaller than a new stage and does not justify changing Stage E's core goal.
- Impact: Stage E stays active with the same long-term outcome, but the immediate active task temporarily shifts from
  `stage-e-02` to `stage-e-05` until the bounded localization pass completes.
- Related Task: `tasks/stage-e-05-static-surface-chinese-localization.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-28-052
- Date: 2026-03-28
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-e-05 bounded Chinese-localization pass
- Context: Stage E was already opened for Support and Job workbench productization, but the live public demo still exposed a mixed Chinese-English static surface across the frontend, public-demo templates, scenario display copy, and directly surfaced backend errors.
- Choice: complete `stage-e-05` as one bounded localization pass, convert the live public demo's user-visible static copy to a Chinese-first baseline without renaming module product names or changing model-output behavior, archive `stage-e-05`, and restore `stage-e-02` as the active Stage E task.
- Why: the live public demo needed a coherent Chinese-first presentation before deeper Support and Job workbench state was added on top of it.
- Impact: the public demo's main path is now Chinese-first at the static-surface level, major backend errors shown directly to users are localized, built-in demo templates and seeded content are localized, and Stage E workbench execution can now resume on a cleaner showcase baseline.
- Related Task: `tasks/archive/stage-e/stage-e-05-static-surface-chinese-localization.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-28-053
- Date: 2026-03-28
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-e-02 Support case workbench foundation
- Context: Stage E opened to turn non-Research modules into persistent workbench surfaces, but Support still stored most durable collaboration value in follow-up task chains and per-task results instead of in a reusable case object.
- Choice: add persistent `support_case` and `support_case_event` primitives, synchronize completed Support tasks into durable case timelines and bounded case status metadata, expose Support case APIs and a Support workbench section in the UI, archive `stage-e-02`, and move the active Stage E task to `stage-e-03`.
- Why: Support needed a first persistent workbench surface that makes follow-up and escalation continuity readable without pretending the shared task runtime should be replaced by a separate ticketing product.
- Impact: the platform now preserves one durable Support case object with case-level history, latest summary, owner guidance, evidence status, and task-linked timeline entries; the live public demo can now show Support workbench depth beyond raw task history; and Stage E can move on to Job hiring workbench depth while keeping the Support case baseline in place.
- Related Task: `tasks/archive/stage-e/stage-e-02-support-case-workbench-foundation.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-28-054
- Date: 2026-03-28
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-e-03 Job hiring workbench foundation
- Context: Stage E opened to turn non-Research modules into persistent workbench surfaces, but Job Assistant still stored durable hiring context mainly inside isolated task outputs and comparison chains instead of in one reusable hiring object.
- Choice: add persistent `job_hiring_packet` and `job_hiring_packet_event` primitives, synchronize completed Job tasks into durable packet timelines and bounded shortlist history, expose Job hiring-packet APIs and a Job workbench section in the UI, archive `stage-e-03`, and move the active Stage E task to `stage-e-04`.
- Why: Job needed a first persistent workbench surface that keeps candidate comparison and shortlist state readable without pretending the shared task runtime should be replaced by a full ATS product.
- Impact: the platform now preserves one durable Job hiring packet with packet-level history, candidate-pool continuity, shortlist refresh history, and task-linked timeline entries; the live public demo can now show Job workbench depth beyond raw task history; and Stage E can move on to public-demo continuity once both Support and Job workbench foundations exist.
- Related Task: `tasks/archive/stage-e/stage-e-03-job-hiring-workbench-foundation.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-28-055
- Date: 2026-03-28
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-e-04 public-demo workbench continuity
- Context: once Support cases and Job hiring packets became persistent public-demo-visible objects, the live demo no longer had an honest continuity story if operators or viewers assumed old workbench state would be silently cleaned up between walkthroughs.
- Choice: define one bounded continuity contract for the live public demo, document that existing workspace state may keep accumulated Support case and Job hiring-packet history, extend the operator refresh and smoke guidance accordingly, add user-visible continuity notes on the guided-workspace and module-task surfaces, archive `stage-e-04`, and leave the next Stage E direction open for human confirmation.
- Why: Stage E needed an honest demo-continuity story before opening another workbench wave, and that story had to avoid hidden manual cleanup or vague operator memory.
- Impact: operators now have one explicit rule for when to preserve versus replace workspaces in the public demo, Support and Job workbench persistence no longer relies on unwritten cleanup assumptions, and outside viewers get a clear explanation that a clean walkthrough should come from a fresh guided demo workspace rather than an implied page-level reset.
- Related Task: `tasks/archive/stage-e/stage-e-04-public-demo-workbench-continuity.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-28-056
- Date: 2026-03-28
- Status: Confirmed
- Source: Human + Planning
- Topic: define the second Stage E task wave
- Context: the first Stage E wave completed the foundation layer for Support cases, Job hiring packets, and bounded public-demo continuity, but those workbench objects are still closer to readable persistence than to direct work surfaces.
- Choice: keep Stage E open, define the second Stage E wave as `stage-e-07`, `stage-e-08`, and `stage-e-09`, focus that wave on Support case action loops, Job hiring-packet action loops, and workbench-first public-demo walkthrough clarity, archive the planning task as `stage-e-06`, and move the active Stage E task to `stage-e-07`.
- Why: the next meaningful bounded step is to make the new workbench objects directly usable without expanding Stage E into a broad ticketing or ATS product.
- Impact: Stage E now has an explicit second wave aimed at actionable workbench behavior, and the control plane points at one concrete next task instead of an open-ended continuation.
- Related Task: `tasks/archive/stage-e/stage-e-06-wave-two-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-28-057
- Date: 2026-03-28
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-e-07 Support case action loop
- Context: the first Stage E wave introduced persistent Support cases, but users still had to remember task history and manually reconstruct the next follow-up instead of working from the case object itself.
- Choice: add one bounded Support case action-loop contract, expose case-level action guidance in Support case responses, let the Support workbench seed the next follow-up task directly from a case, rewrite the Support module task surface in clean Chinese-first UTF-8 copy, archive `stage-e-07`, and move the active Stage E task to `stage-e-08`.
- Why: Stage E should make Support cases directly usable without bypassing the shared task runtime or drifting into a broader ticketing product.
- Impact: Support cases can now drive the next follow-up action directly, case-status progression is visible at the case surface instead of being inferred from raw task history, and the live public demo can explain the Support action loop honestly from the case workbench itself.
- Related Task: `tasks/archive/stage-e/stage-e-07-support-case-action-loop.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-28-058
- Date: 2026-03-28
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-e-08 Job hiring packet action loop
- Context: the first Stage E wave introduced persistent Job hiring packets, but users still had to remember task history and manually reconstruct the next shortlist refresh or candidate review instead of working from the packet object itself.
- Choice: add one bounded Job hiring-packet action-loop contract, expose packet-level action guidance and recent note context in Job hiring-packet responses, let the Job workbench seed the next hiring task directly from a packet, archive `stage-e-08`, and move the active Stage E task to `stage-e-09`.
- Why: Stage E should make Job hiring packets directly usable without bypassing the shared task runtime or drifting into a broader ATS product.
- Impact: Job hiring packets can now drive shortlist refresh and follow-on candidate review directly, packet-level review notes are readable at the packet surface, and the live public demo can explain the Job action loop honestly from the packet workbench itself.
- Related Task: `tasks/archive/stage-e/stage-e-08-job-hiring-packet-action-loop.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-28-059
- Date: 2026-03-28
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-e-09 public demo workbench entry and walkthrough
- Context: after `stage-e-07` and `stage-e-08`, the live public demo exposed direct Support case and Job hiring-packet actions, but viewers still needed a clearer rule for when to start from a fresh guided workspace versus when to continue from an existing workbench object.
- Choice: clarify the public-demo entry rule in the workspace overview, module task surfaces, and operator-facing docs so new viewers start from a fresh guided demo workspace while existing Support and Job work continues from the visible case or hiring-packet workbench; archive `stage-e-09` and leave the next Stage E direction open for human confirmation.
- Why: the Stage E second wave should close with one honest walkthrough story instead of relying on hidden operator narration or implying silent page-level reset.
- Impact: the live public demo now explains the fresh-workspace path and the workbench-first continuation path consistently, and Stage E can now be reviewed for closeout or another bounded wave.
- Related Task: `tasks/archive/stage-e/stage-e-09-public-demo-workbench-entry-and-walkthrough.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-28-060
- Date: 2026-03-28
- Status: Confirmed
- Source: Human + Planning
- Topic: close Stage E after the second workbench wave
- Context: Stage E opened to turn Support and Job from isolated task-result workflows into persistent workbench surfaces. After `stage-e-07`, `stage-e-08`, and `stage-e-09`, both non-Research modules now have durable work objects, direct workbench action loops, and an honest public-demo continuation story.
- Choice: close Stage E as complete, preserve its Support case and Job hiring-packet workbench depth as the current platform baseline, and move the next planning focus away from additional Stage E workbench depth.
- Why: Stage E's bounded goal has been met; keeping it open would blur the stage boundary and mix workbench productization with a separate user-experience restructuring problem.
- Impact: Support cases, Job hiring packets, and the public-demo continuity rule now become baseline platform behavior instead of active Stage E experiments, and the next stage can focus on the user-facing surface without reopening Stage E scope.
- Related Task: `tasks/archive/stage-e/stage-e-09-public-demo-workbench-entry-and-walkthrough.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-28-061
- Date: 2026-03-28
- Status: Confirmed
- Source: Human + Planning
- Topic: define Stage F as a public-demo experience reset
- Context: the project now has a working live public demo and durable Support / Job workbench objects, but the user-facing surface still exposes too much internal structure, has weak hierarchy, and does not clearly explain where a first-time viewer should start or how the three scenario modules differ.
- Choice: open `Stage F: Public Demo Experience Clarification and UX Reset` as a separate planning unit focused on information architecture, navigation clarity, module positioning, and showcase-ready front-end presentation without renaming the three module products.
- Why: these user-facing problems are real product-surface problems, not just cosmetic polish, and they should be treated as a bounded stage before the roadmap returns to deeper trust, eval, and AI-capability work.
- Impact: the project now has one explicit stage for reducing cognitive load, clarifying hierarchy, and making the demo easier to understand and present, while leaving the long-term roadmap and module names intact.
- Related Task: `tasks/archive/stage-f/stage-f-01-task-stack-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-28-062
- Date: 2026-03-28
- Status: Confirmed
- Source: Human + Planning
- Topic: define the first Stage F task wave
- Context: Stage F should improve the user-facing experience in a bounded order instead of starting with one broad front-end rewrite that mixes hierarchy, module explanation, and visual polish all at once.
- Choice: define the first Stage F wave as `stage-f-02`, `stage-f-03`, `stage-f-04`, and `stage-f-05`, start with home/workspace information architecture, then simplify workspace navigation and primary flow, then clarify module entry surfaces, and leave visual-system polish as the final step in the wave.
- Why: structure and hierarchy should be fixed before visual styling; otherwise the project would produce a nicer-looking but still confusing demo.
- Impact: Stage F now has one explicit, ordered UX-reset wave with `stage-f-02` as the active task, and the control plane can track the experience redesign without losing scope discipline.
- Related Task: `tasks/archive/stage-f/stage-f-01-task-stack-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-28-063
- Date: 2026-03-28
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-f-02 home and workspace information-architecture reset
- Context: Stage F opened because the live public demo and workspace center exposed too much platform structure too early. First-time users had to simultaneously parse demo limits, templates, deep links, workspaces, and module explanations instead of being shown one primary start path.
- Choice: simplify the home page into a clearer first-time versus returning-user split, demote public-demo limits and deeper platform detail behind lighter disclosure, rebuild the workspace center around first-time guided-demo creation versus existing-work continuation, archive `stage-f-02`, and move the active Stage F task to `stage-f-03`.
- Why: the user-facing surface needed structural simplification before any deeper navigation or visual redesign could be trustworthy.
- Impact: first contact with the live demo is now more legible, the workspace center no longer treats deep links and raw workspace lists as equal entry points, and Stage F can move on to workspace hierarchy and primary-flow simplification.
- Related Task: `tasks/archive/stage-f/stage-f-02-home-and-workspace-information-architecture-reset.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-28-064
- Date: 2026-03-28
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-f-03 workspace navigation and primary-flow simplification
- Context: after `stage-f-02`, first-time entry into the public demo and workspace center was clearer, but users still entered each workspace through a flat list of equal pages. Overview, modules, documents, chat, tasks, and analytics still competed as peer-level surfaces, which made return paths unclear and hid the intended main workflow.
- Choice: add one explicit workspace-page shell with breadcrumb navigation, grouped primary versus secondary workspace navigation, and one visible main flow across `documents -> chat -> tasks`; archive `stage-f-03`; and move the active Stage F task to `stage-f-04`.
- Why: Stage F needed to solve workspace hierarchy before it could credibly explain module differences or move on to showcase-oriented visual polish.
- Impact: workspace pages now communicate where the user is, how to return to the workspace center or overview, which surfaces belong to the main workflow, and why analytics is a secondary review surface instead of a first-stop page.
- Related Task: `tasks/archive/stage-f/stage-f-03-workspace-navigation-and-primary-flow-simplification.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-29-065
- Date: 2026-03-29
- Status: Confirmed
- Source: Human
- Topic: rescope the remaining Stage F wave around a single workspace workbench
- Context: after the first two Stage F tasks, the workspace hierarchy became clearer, but the user still had to navigate several separate pages for overview, modules, documents, chat, and tasks. The human clarified that this still feels like a developer console rather than a product workbench.
- Choice: replace the old remaining Stage F sequence with a new order: `stage-f-04-workspace-workbench-consolidation`, then `stage-f-05-module-positioning-inside-workbench`, then `stage-f-06-demo-visual-system-and-showcase-polish`.
- Why: module explanation and visual polish will be easier to do correctly once the workspace no longer depends on a flat multi-page model.
- Impact: the next active Stage F task is now the single-workbench consolidation; module-positioning work moves behind that structural reset; visual polish remains the final step of the wave.
- Related Task: `tasks/stage-f-04-workspace-workbench-consolidation.md`
- Supersedes: `tasks/stage-f-04-module-positioning-and-entry-surface-clarification.md`

## Decision Entry

- ID: DEC-2026-03-29-066
- Date: 2026-03-29
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-f-04 workspace workbench consolidation
- Context: after `stage-f-02` and `stage-f-03`, users could better understand where to start, but the workspace still asked them to treat overview, modules, documents, chat, and tasks as separate peer pages. The human clarified that this still felt like a developer console rather than a product workbench.
- Choice: collapse the primary workspace path into one main workbench, move documents, chat, and tasks behind panel-level switching on that surface, demote analytics to the only secondary workspace page, preserve compatibility redirects for legacy deep links, archive `stage-f-04`, and move the active Stage F task to `stage-f-05`.
- Why: Stage F needed to finish the structural reset before module positioning or visual polish could be credible.
- Impact: users now enter each workspace through one obvious main workbench instead of a flat page list, old deep links continue to land in the correct panel without pretending those pages still define the main model, and the next bounded step can focus on clarifying module differences inside the new workbench itself.
- Related Task: `tasks/archive/stage-f/stage-f-04-workspace-workbench-consolidation.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-29-067
- Date: 2026-03-29
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-f-05 module positioning inside the workbench
- Context: after `stage-f-04`, the workspace finally had one primary workbench, but the three modules still risked feeling like similar text-analysis tools because the workbench itself did not explain their different work objects, outputs, and continuation rules early enough.
- Choice: move module explanation into the unified workbench, add one positioning card grounded in the scenario registry, make the documents/chat/tasks region descriptions module-specific, archive `stage-f-05`, and move the active Stage F task to `stage-f-06`.
- Why: Stage F needed users to understand why Research, Support, and Job are different before visual polish would have real product value.
- Impact: module differentiation now shows up in the main workbench surface itself, Support case and Job hiring-packet continuity are explained earlier than deep workbench history, and the last bounded Stage F step can focus on showcase-ready visual quality instead of structural explanation.
- Related Task: `tasks/archive/stage-f/stage-f-05-module-positioning-inside-workbench.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-31-068
- Date: 2026-03-31
- Status: Confirmed
- Source: Human + Planning
- Topic: redefine the remaining Stage F wave around personal-homepage separation and a chat-first workbench
- Context: after `stage-f-05`, the workspace explains the three modules more clearly, but the human clarified that the overall product still feels wrong in two ways: the root home page and project-facing home still overlap too much, and the workspace still feels more like a panelized tool console than a chat-centered product workbench.
- Choice: supersede the old standalone `stage-f-06` visual-polish task, define a new Stage F second wave as `stage-f-07`, `stage-f-08`, `stage-f-09`, `stage-f-10`, and `stage-f-11`, treat the root home page as a personal homepage, treat the project home as the workspace center, move the workbench toward a chat-first model with summonable supporting surfaces, archive the replanning task, and move the active Stage F task to `stage-f-07`.
- Why: visual polish alone would improve appearance but would not solve the deeper product-shape problem that the human identified.
- Impact: Stage F now continues with a second bounded wave that changes the site and workbench structure before the final showcase-polish step, while keeping the module names and Stage E workbench behavior intact.
- Related Task: `tasks/archive/stage-f/stage-f-06-wave-two-replanning.md`
- Supersedes: `tasks/archive/stage-f/stage-f-06-demo-visual-system-and-showcase-polish-superseded.md`

## Decision Entry

- ID: DEC-2026-03-31-069
- Date: 2026-03-31
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-f-07 personal homepage and project-entry split
- Context: the new Stage F second wave begins by separating the root site from the product itself. Before this task, the root home page still behaved too much like the project entry surface, which made the site feel repetitive and blurred the line between the personal homepage and the product.
- Choice: rewrite the root `/` page as a personal homepage plus project directory, introduce `/app` as the dedicated project-facing entry route, update auth return paths to land on that project-facing route, archive `stage-f-07`, and move the active Stage F task to `stage-f-08`.
- Why: the human explicitly clarified that the root site should not double as the internal entry surface for a single project.
- Impact: the public site now has one clearer external-facing role, the project has one clearer internal-facing entry route, and the next bounded step can simplify the project-facing home itself instead of continuing to untangle the root page.
- Related Task: `tasks/archive/stage-f/stage-f-07-personal-homepage-and-project-entry-split.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-31-070
- Date: 2026-03-31
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-f-08 project-home workspace-center reset
- Context: once the root personal homepage and project-facing entry route were separated, the project still needed its own home surface to become lighter and more product-like. Before this task, `/app` was only a temporary landing page and the older `/workspaces` page still held the heavy workspace-center surface.
- Choice: move the lighter workspace-center surface onto `/app`, keep one lightweight guided-demo entry, bound the existing-work list inside a fixed-height scroll region, rewrite the workspace-center and public-demo notice copy into clean UTF-8 Chinese, redirect `/workspaces` into `/app`, archive `stage-f-08`, and move the active Stage F task to `stage-f-09`.
- Why: the project-facing home should behave like the real start point for this product instead of remaining a temporary landing page or another duplicated explanation surface.
- Impact: the project now has one clearer internal home, returning users can continue work from a bounded list instead of a page that expands without bound, and the next bounded step can focus directly on making the workspace itself chat-first.
- Related Task: `tasks/archive/stage-f/stage-f-08-project-home-workspace-center-reset.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-31-071
- Date: 2026-03-31
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-f-09 chat-first workbench shell
- Context: after `stage-f-08`, the project had a clearer root-site split and a lighter project-facing home, but the main workspace still read too much like a balanced panel console. Chat, documents, and task actions still competed too evenly for attention, which kept the workbench from feeling like one primary product surface.
- Choice: make chat the default center of the workspace, demote documents into a lighter compact supporting surface, demote task work into a supporting action area instead of a peer page, archive `stage-f-09`, and move the active Stage F task to `stage-f-10`.
- Why: the human explicitly clarified that the product should read more like one chat-centered workbench with supporting affordances than like a console of equal tool regions.
- Impact: the primary workspace now reads more like one object-aware workbench, users no longer need to interpret documents and task work as equal first-stop regions, and the next bounded step can focus on making supporting detail and analytics feel truly summonable rather than just smaller.
- Related Task: `tasks/archive/stage-f/stage-f-09-chat-first-workbench-shell.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-31-072
- Date: 2026-03-31
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-f-10 supporting panels and analytics drawer
- Context: after `stage-f-09`, the workspace already read as a chat-first shell, but supporting detail still behaved too much like a persistent block or a separate page destination. The human had explicitly clarified that analytics should be summoned by button instead of living as a constant first-stop surface.
- Choice: turn documents, task actions, execution detail, and analytics into on-demand supporting surfaces, route the older analytics page into the workbench analytics surface for compatibility, archive `stage-f-10`, and move the active Stage F task to `stage-f-11`.
- Why: the workbench should keep one obvious center while still exposing honest operational detail when the user needs it.
- Impact: the workspace now feels closer to one object-aware chat-first product surface, analytics no longer competes as a persistent page-level destination, and the final bounded Stage F step can focus on showcase-ready visual polish rather than more structural cleanup.
- Related Task: `tasks/archive/stage-f/stage-f-10-supporting-panels-and-analytics-drawer.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-31-073
- Date: 2026-03-31
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-f-11 showcase visual polish
- Context: after `stage-f-10`, the site structure and workbench model were finally in the right shape, but the highest-traffic pages still looked too plain and still carried presentation defects that weakened trust. The last bounded Stage F task existed specifically to improve those highest-traffic surfaces without reopening structure work.
- Choice: apply one bounded showcase-quality visual pass across the root personal homepage, the project-facing home, the workspace center, the chat-first workbench shell, and the main chat surface; archive `stage-f-11`; and leave Stage F closeout open for human confirmation.
- Why: the project needed one final polish step after the structural reset so the public demo would feel more intentional and presentable instead of staying in an internal-tool visual state.
- Impact: the Stage F second wave is now execution-complete, the highest-traffic surfaces are materially stronger for live demo use, and the next step is a human decision about Stage F closeout rather than another default implementation task.
- Related Task: `tasks/archive/stage-f/stage-f-11-showcase-visual-polish.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-31-074
- Date: 2026-03-31
- Status: Confirmed
- Source: Human + Planning
- Topic: replace Stage F closeout with a third bounded UX-restructure wave
- Context: after reviewing the post-`stage-f-11` surface, the human clarified that the product still feels too verbose, too single-column, and too panelized. The direction from the first two Stage F waves is still correct, but the project-facing home still repeats too much explanation, the existing-work region still dominates too much space, and the main workspace still exposes documents, task work, and analytics more visibly than the intended product model.
- Choice: keep Stage F open, archive one replanning task, and define a third bounded Stage F wave centered on a denser viewport-first project home, a conversation-first workbench rebuild, lighter summoned supporting surfaces, and one final cleanup / visual pass after structure lands.
- Why: closing Stage F at this point would lock in the wrong interaction model and force later roadmap stages to build on top of a front-end shape the human has already rejected.
- Impact: Stage F now continues with a third bounded wave instead of closing; the next active task becomes `stage-f-13`, and the repo should treat the current UI as a transitional baseline rather than the final Stage F endpoint.
- Related Task: `tasks/archive/stage-f/stage-f-12-wave-three-replanning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-31-075
- Date: 2026-03-31
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-f-13 personal homepage and project-home viewport reset
- Context: after replanning the third Stage F wave, the first required step was to compress the root personal homepage and the `/app` project-facing home into denser, more scannable first-view surfaces. Before this task, both routes still carried too much vertical explanation and too much single-column weight.
- Choice: rebuild the root personal homepage around one denser two-column hero plus compact support cards, rebuild `/app` around one lighter project header plus a denser workspace-center layout, keep guided demo as the first-time entry, keep existing workspaces inside one bounded scroll region, archive `stage-f-13`, and move the active Stage F task to `stage-f-14`.
- Why: the human explicitly clarified that the site should communicate the primary story and actions inside one clearer viewport instead of depending on extra scrolling and repeated explanatory copy.
- Impact: the product now has a stronger personal-home versus project-home split, the project-facing home is materially lighter and more scannable, and the remaining third-wave work can now focus on the workspace interaction model itself.
- Related Task: `tasks/archive/stage-f/stage-f-13-personal-homepage-and-project-home-viewport-reset.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-31-076
- Date: 2026-03-31
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-f-14 conversation-first workbench rebuild
- Context: after `stage-f-13`, the site entry surfaces were denser and clearer, but the main workspace still read too much like a visible set of peer panels. The human had explicitly clarified that the workbench should feel closer to one conversation surface where documents and task work are lightweight affordances rather than balanced destinations.
- Choice: rebuild the main workspace around one conversation-first center, rewrite the main chat surface to act like the obvious work area, demote documents into lighter context/upload controls, demote task work into module-aware next-action affordances, archive `stage-f-14`, and move the active Stage F task to `stage-f-15`.
- Why: Stage F needed to finish the core interaction-model reset before it could credibly refine summoned supporting detail or perform final cleanup.
- Impact: the workspace now reads more like one product workbench instead of a tool console, Support case and Job hiring-packet continuity stay visible inside that workbench, and the next bounded step can focus on analytics, operator detail, and other summoned supporting surfaces.
- Related Task: `tasks/archive/stage-f/stage-f-14-conversation-first-workbench-rebuild.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-31-077
- Date: 2026-03-31
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-f-15 summoned supporting surfaces and operator affordances
- Context: after `stage-f-14`, the main workspace already centered on one conversation-first surface, but supporting detail still risked reading like visible product structure instead of clearly secondary affordances. The human had explicitly clarified that analytics should be opened by button rather than treated like a standing page destination.
- Choice: keep the main conversation surface intact, compress the visible document affordance further, move deeper document detail, module actions, analytics, and operator-oriented execution detail behind explicit summoned surfaces, archive `stage-f-15`, and move the active Stage F task to `stage-f-16`.
- Why: Stage F needed one honest supporting-detail layer before the final visual cleanup could be done on top of a stable interaction model.
- Impact: the workspace now distinguishes the main work surface from secondary detail much more clearly, compatibility analytics routes still land in the right place, and the final Stage F task can now focus on visual-system cleanup and legacy removal instead of more structural changes.
- Related Task: `tasks/archive/stage-f/stage-f-15-summoned-supporting-surfaces-and-operator-affordances.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-31-078
- Date: 2026-03-31
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-f-16 showcase visual redesign and legacy cleanup
- Context: after `stage-f-15`, the structural interaction model was finally in the right shape, but the highest-traffic surfaces still needed one coherent visual pass and one last cleanup sweep. The remaining goal was not another structural rewrite; it was to make the new shape look intentional enough for external showcase use and to remove the last obvious rough edges from the front-end surface.
- Choice: apply the final Stage F visual redesign across the root personal homepage, the `/app` project home, the workspace center, the chat-first workbench, the document surface, and the shared card system; archive `stage-f-16`; and return Stage F to human closeout review instead of auto-extending the stage again.
- Why: the human had explicitly clarified that the front-end should be treated as a product-surface rebuild, not a patchwork cleanup, and the third follow-up wave needed a real finish line before any later roadmap work resumed.
- Impact: the personal homepage versus project-home split now reads more intentionally, the workbench visual system is more coherent around one conversation-first center, and the remaining question is now stage closeout rather than another active implementation gap.
- Related Task: `tasks/archive/stage-f/stage-f-16-showcase-visual-redesign-and-legacy-cleanup.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-31-079
- Date: 2026-03-31
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-f-17 narrow workbench density and direct-affordance follow-up
- Context: after `stage-f-16`, the overall Stage F direction was finally right, but human review still identified a few narrow workbench usability issues: the visible top of the conversation surface was still too tall, some cards repeated the same explanation, the document upload affordance was too weak, and abstract action labels still hid what the user would actually get.
- Choice: define one narrow post-wave follow-up, compress the workbench top area and chat empty state, reduce repeated explanation, rename abstract action language into more result-oriented labels, add drag-and-drop plus click-to-select upload while keeping an explicit upload button, archive `stage-f-17`, and return Stage F to final human closeout review.
- Why: these gaps were too small to justify another broad Stage F wave, but too visible to ignore before deciding whether the stage could close.
- Impact: the workbench now wastes less vertical space, the visible surface is more direct about what to do next, document upload is easier to discover and use, and the remaining question is now Stage F closeout rather than more active UX rework inside this stage.
- Related Task: `tasks/archive/stage-f/stage-f-17-workbench-density-and-direct-affordances.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-03-31-080
- Date: 2026-03-31
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-f-18 project-home and research-workflow reset
- Context: after `stage-f-17`, human review made it clear that the remaining front-end gaps were no longer small density issues. The `/app` surface still behaved too much like a workspace-center explanation page, and the main workbench still read too much like a generic explanatory chat surface instead of one research workflow page with a clear primary path.
- Choice: define and complete `stage-f-18`, rebuild `/app` into a denser project start surface with top-level login or session actions, one lightweight guided-demo row, one manual-create surface, and one bounded existing-work region; rebuild the main workspace so the left side reads as a research workflow with clickable prompt chips, an obvious `瀵偓婵鍨庨弸鎭?CTA, and visible analysis progress in the main column; archive the task; and return Stage F to final closeout review instead of extending the stage again by default.
- Why: the human had already confirmed that the front-end should be treated as a product-surface rebuild, not as a series of small explanation edits. The remaining gap was about product shape: start surfaces, workflow hierarchy, and how the main analysis path competes against supporting detail.
- Impact: the root homepage and `/app` surface are now more clearly separated, the project-facing home behaves more like a true product entry surface, and the main workspace is closer to a research workflow page with clearer hierarchy between prompting, analysis, supporting state, and formal output. Stage F now returns to closeout review with one more coherent end state.
- Related Task: `tasks/archive/stage-f/stage-f-18-project-home-and-research-workflow-reset.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-04-01-081
- Date: 2026-04-01
- Status: Confirmed
- Source: Human
- Topic: close Stage F and open Stage G
- Context: Stage F completed the user-facing experience reset through the final project-home and research-workflow
  follow-up, and the next bounded need is no longer front-end shape iteration but deployment-boundary correction.
- Choice: close Stage F as complete and open `Stage G: Multi-Subdomain Product Split and Shared Edge Routing`.
- Why: the repo now needs a new planning unit that focuses on product-only host boundaries and shared-edge deployment
  instead of continuing to stretch the UX-reset stage.
- Impact: control-plane docs move from Stage F closeout review into a new active Stage G task stack.
- Related Task: `tasks/archive/stage-g/stage-g-01-task-stack-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-04-01-082
- Date: 2026-04-01
- Status: Confirmed
- Source: Human
- Topic: product-only multi-subdomain deployment target
- Context: the commercial deployment shape is now explicitly defined around a separate root homepage plus a dedicated
  product frontend and API. The old `app.<domain>` public-demo shape is not the long-term boundary for this repo.
- Choice: treat `lmpai.online` as the separate homepage outside this repo, adapt this repository to the dedicated
  product frontend at `weave.lmpai.online`, keep the backend API at `api.lmpai.online`, and support that target behind
  one Cloudflare -> Caddy -> multi-service edge with host-based routing, split service deployment, explicit
  reverse-proxy headers, and explicit CORS.
- Why: a commercial multi-project setup needs the root marketing site, the product frontend, and the API to evolve and
  deploy independently.
- Impact: the repo now needs one product-only root route, one compatibility redirect from `/app`, one dedicated
  shared-edge deployment path, and deployment docs/templates that no longer assume `app.<domain>` as the canonical
  product host.
- Related Task: `tasks/stage-g-02-weave-subdomain-product-split.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-04-01-083
- Date: 2026-04-01
- Status: Confirmed
- Source: Human
- Topic: Stage G closeout
- Context: the host-boundary split is now live, the root homepage is deployed outside this repo, and this repository
  now serves only the dedicated `weave` product frontend plus `api` backend stack.
- Choice: close Stage G and archive `tasks/stage-g-02-weave-subdomain-product-split.md`.
- Why: the bounded deployment-boundary objective has been achieved and should not remain the active planning unit.
- Impact: control-plane docs should now treat Stage G as complete and closed.
- Related Task: `tasks/archive/stage-g/stage-g-02-weave-subdomain-product-split.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-04-01-084
- Date: 2026-04-01
- Status: Confirmed
- Source: Human
- Topic: next bounded stage after the host split
- Context: the deployment-boundary work is complete and the long-term roadmap's next major theme is the first staged
  AI-capability wave around a more modern model interface and bounded built-in or tool-assisted behavior.
- Choice: open `Stage H: Model Interface Modernization and Tool-Visible Research Pilot`.
- Why: the repo now has the right commercial host boundary and can return to product learning and capability growth in
  one bounded, publicly demonstrable way.
- Impact: Stage H becomes the active planning unit and Research remains the reference workflow for the first pilot.
- Related Task: `tasks/archive/stage-h/stage-h-01-task-stack-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-04-01-085
- Date: 2026-04-01
- Status: Confirmed
- Source: Human
- Topic: Stage H first task wave
- Context: Stage H needs one bounded first wave that modernizes the model-facing interface without exploding scope.
- Choice: define the first Stage H wave as:
  - `tasks/stage-h-02-responses-style-model-interface-foundation.md`
  - `tasks/stage-h-03-research-tool-assisted-analysis-pilot.md`
  - `tasks/stage-h-04-tool-trace-and-eval-visibility.md`
- Why: the new wave should first build one shared contract, then one visible Research pilot, then one trace and eval
  honesty layer around that pilot.
- Impact: the repo now has one concrete Stage H task stack and one primary active task.
- Related Task: `tasks/archive/stage-h/stage-h-01-task-stack-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-04-01-086
- Date: 2026-04-01
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-h-02 shared model-interface foundation
- Context: Stage H needed one shared foundation before any bounded tool-assisted workflow could become durable. The repo
  had three separate OpenAI-compatible call paths for chat generation, embeddings, and eval judging.
- Choice: add one shared backend model-interface service, route the existing OpenAI-compatible chat, embedding, and
  eval provider calls through it, archive `stage-h-02`, and move the active task to the Research-first pilot.
- Why: the next Stage H work should build on one reusable contract instead of on scattered provider-specific logic.
- Impact: the repo now has one shared model-interface layer under the current provider path, and future tool-visible
  capability work can extend that layer without reopening the deployment-boundary stage.
- Related Task: `tasks/archive/stage-h/stage-h-02-responses-style-model-interface-foundation.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-04-01-087
- Date: 2026-04-01
- Status: Confirmed
- Source: Human + Implementation
- Topic: runtime upload storage should not be repo-tracked
- Context: the repository still tracked a few files under `server/storage/uploads/`, which caused local runtime upload
  churn to appear as source changes even though deployed product data now lives behind runtime volumes and should not be
  versioned as code.
- Choice: add `server/storage/uploads/` to `.gitignore`, remove already tracked upload files from the Git index, and
  treat that directory as runtime-only state going forward.
- Why: uploaded source files are local or deployed runtime data, not durable repo content, and they should not pollute
  normal feature work or control-plane task history.
- Impact: future local upload churn should stop appearing as code changes, while deployment data remains governed by the
  runtime volume boundary instead of by Git.
- Related Task: `tasks/archive/stage-h/stage-h-05-runtime-upload-storage-ignore-cleanup.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-04-01-088
- Date: 2026-04-01
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-h-03 Research tool-assisted analysis pilot
- Context: Stage H needed one visible bounded capability pilot on top of the shared model-interface foundation, but it
  still needed to stay inside the existing Research workspace flow instead of becoming a separate experimental surface.
- Choice: add one `research_tool_assisted` chat mode for Research workspaces, route it through a new bounded
  Research-only tool-assisted service, expose inline tool-step summaries in the chat response, archive `stage-h-03`,
  and move the active task to trace/eval visibility follow-through.
- Why: the first visible capability wave should demonstrate modern tool-assisted analysis behavior in one honest,
  product-facing path before any broader rollout or deeper orchestration work begins.
- Impact: the repo now has one user-visible Research pilot built on the new model-interface layer, and the next active
  work can focus on trace and eval visibility instead of on basic capability wiring.
- Related Task: `tasks/archive/stage-h/stage-h-03-research-tool-assisted-analysis-pilot.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-04-01-089
- Date: 2026-04-01
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-h-04 tool trace and eval visibility
- Context: the first Stage H pilot was live, but its tool-assisted behavior still risked looking like a black box unless
  the traces became human-readable and one bounded regression baseline checked for visible tool behavior plus honest
  degraded no-source handling.
- Choice: make the Research pilot trace surface show planning focus, search query, visible tool steps, and degraded
  reason; add one bounded regression-facing evaluator for tool-step visibility and honest degraded paths; archive
  `stage-h-04`; and return Stage H to human selection of the next bounded task wave.
- Why: the first capability wave should end with an honest inspection baseline rather than with a hidden or generic
  success-only surface.
- Impact: Stage H first wave is now complete, the Research pilot is inspectable enough for honest review, and the next
  bounded capability step can be chosen from a more stable baseline.
- Related Task: `tasks/archive/stage-h/stage-h-04-tool-trace-and-eval-visibility.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-04-01-090
- Date: 2026-04-01
- Status: Confirmed
- Source: Human + Planning
- Topic: define the second Stage H capability wave
- Context: the first Stage H wave delivered one shared model-interface foundation, one visible bounded Research
  tool-assisted pilot, and one honest trace/eval review baseline. The roadmap still warns against jumping too early
  into connector work or multi-agent orchestration before the bounded capability layer learns background execution,
  context compaction, and replay discipline in one workflow.
- Choice: keep Stage H active and define a second bounded Research-first wave: move the current pilot toward
  background-capable analysis runs, add bounded conversation-state compaction and run memory, and add tool-aware replay
  plus stronger regression review before any broader connector or orchestration expansion.
- Why: the next learning step should deepen the existing visible Research path instead of broadening the new
  model-interface layer into multiple modules or trend-driven agent work too early.
- Impact: Stage H now has one second-wave task stack and one new primary active task, while the roadmap remains aligned
  to Wave 1 model-interface and built-in-tool learning rather than prematurely opening Wave 2 or Wave 3.
- Related Task: `tasks/archive/stage-h/stage-h-06-wave-two-planning.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-04-01-091
- Date: 2026-04-01
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-h-07 Research background analysis runs
- Context: the first Stage H second-wave task needed to deepen the visible Research pilot without jumping into broader multi-agent orchestration. The pilot still behaved like a synchronous chat turn even though the roadmap now needed one bounded background-capable run path.
- Choice: add one explicit `research_analysis_run` object plus API, queue, worker, and Research workbench surface; let Research launch bounded background analysis runs on top of the existing tool-assisted pilot; expose queued, running, completed, degraded, and failed run states; archive `stage-h-07`; and move the active task to bounded compaction and run-memory follow-through.
- Why: the next learning step should make the existing visible pilot more durable than one chat response while staying honest and bounded on the same workspace surface instead of broadening into a new orchestration layer too early.
- Impact: Research now has one persisted background-run path with visible status, answer delivery, tool-step summaries, and trace linkage, and the next active work can focus on compaction and replay discipline instead of on basic background execution wiring.
- Related Task: `tasks/archive/stage-h/stage-h-07-research-background-analysis-runs.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-04-02-092
- Date: 2026-04-02
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-h-08 Research context compaction and run memory
- Context: `stage-h-07` made the Research pilot durable enough to run in the background, but later passes in the same conversation still had no bounded way to resume key context without growing prompt state or hiding what was carried forward.
- Choice: add one bounded resumed-run memory contract to `research_analysis_run`, persist one compact memory summary on completed or degraded runs, let later runs in the same conversation resume from the latest terminal run, expose that carried-forward memory on both the run surface and the trace-review surface, archive `stage-h-08`, and move the active task to tool-aware replay and regression follow-through.
- Why: the second Stage H wave should learn how durable tool-assisted analysis resumes key state without prematurely becoming a broader agent-memory or orchestration system.
- Impact: Research background runs now have one explicit compaction boundary, later runs can resume from a compact prior summary instead of from unbounded prompt growth, and the replay/regression task can now evaluate a more durable visible contract.
- Related Task: `tasks/archive/stage-h/stage-h-08-research-context-compaction-and-run-memory.md`
- Supersedes:

## Decision Entry

- ID: DEC-2026-04-02-093
- Date: 2026-04-02
- Status: Confirmed
- Source: Human + Implementation
- Topic: complete stage-h-09 tool-aware replay and regression baseline
- Context: `stage-h-08` made resumed Research background runs durable enough to carry one bounded compact memory, but operator review still relied too heavily on raw trace inspection and had no explicit review contract for terminal runs.
- Choice: add one bounded review surface for recent terminal `research_analysis_run` records, map those runs to their persisted traces, apply a replay/regression baseline that checks trace linkage, prompt visibility, tool-step visibility, compact run memory, honest degraded handling, and resumed-memory visibility, archive `stage-h-09`, and return Stage H to human selection of the next bounded wave.
- Why: the second Stage H wave should end with a stronger review discipline for the deeper Research path without pretending the repo already has a full eval optimization platform.
- Impact: recent terminal Research analysis runs can now be reviewed through one explicit operator-facing baseline instead of only through raw trace JSON, and the next Stage H wave can start from a more durable replay/regression contract.
- Related Task: `tasks/archive/stage-h/stage-h-09-tool-aware-replay-and-regression-baseline.md`
- Supersedes:
