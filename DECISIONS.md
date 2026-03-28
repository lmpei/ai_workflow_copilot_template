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
