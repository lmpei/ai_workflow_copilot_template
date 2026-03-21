# Stage B Plan

## Stage Name

`Stage B: Research Workflow Productization With Recoverable Runtime`

## Status

- Status: active
- Opened At: 2026-03-18
- First Task Wave: complete
- Second Task Wave: active

## Position In The Project

Stage B begins after the formal closeout of Stage A. Stage A established structured Research contracts, report assembly,
trust and regression baselines, follow-up lineage, and a lightweight staging rehearsal path. Stage B shifts the project
from foundational Research depth toward reusable workflow assets, recoverable runtime behavior, and more operator-ready
release routines.

## Planning Model

Stage B operates under the same three-track roadmap model:

1. `Research`
2. `Platform Reliability`
3. `Delivery and Operations`

The tracks remain parallel, but not equally weighted. Stage B keeps `Research` as the primary track while requiring
visible progress in runtime recovery and delivery repeatability.

## Priority Model

- Primary track:
  - `Research`
- Required parallel tracks:
  - `Platform Reliability`
  - `Delivery and Operations`

Stage B should not add deeper Research workflow behavior unless the runtime and delivery layers can support that growth.

## Stage Goal

Turn `Research Assistant` from a deepened task/report module into a reusable workflow surface while making the shared
runtime more recoverable and the staging routine more operator-friendly.

## Track 1: Research

### Objective

Move `Research Assistant` from structured task outputs toward a persistent research workbench and asset lifecycle.

### Focus Areas

- saved research briefs and reusable working context
- report revision and update workflows
- comparison across related research runs or report versions
- explicit lifecycle for promoting task results into longer-lived workspace assets

### Expected Outcomes

- users can reopen and continue a research topic without treating every run as a fresh task
- research results can be revised or compared over time
- formal Research assets survive beyond single task outputs
- Research becomes closer to a reusable workspace workflow than a one-shot report generator

## Track 2: Platform Reliability

### Objective

Move the shared runtime from trust baselines to recoverable execution behavior.

### Focus Areas

- clearer cancel, retry, and resume semantics for long-running tasks and evals
- better recovery behavior when workers stop mid-run
- richer runtime state and recovery traces
- regression coverage that keeps Stage B workflow additions from degrading execution trust

### Expected Outcomes

- interrupted work is easier to diagnose and recover
- operator-visible runtime states are clearer than simple pending/running/done/failed boundaries
- Stage B workflow changes can be checked against recovery-aware regression expectations

## Track 3: Delivery and Operations

### Objective

Turn the Stage A staging path into a more repeatable operator routine.

### Focus Areas

- operator-oriented release rehearsal helpers
- handoff/checklist artifacts for staging releases
- clearer capture of what changed, what was verified, and what the rollback target is
- stronger environment conventions around dev and staging inputs

### Expected Outcomes

- a collaborator can rehearse a staging release with less hidden knowledge
- release steps and handoff artifacts become more repeatable
- staging operations stay lightweight but more disciplined than Stage A

## Non-Goals

Stage B does not primarily optimize for:

- deep productization of Support Copilot
- deep productization of Job Assistant
- full production-grade SRE or Kubernetes-scale operations
- major module renaming or branding work
- heavy multi-agent orchestration beyond what the current workflow depth demands

## Execution Rules

- every Stage B Research milestone should pull at least one runtime-recovery improvement with it
- every larger Stage B workflow milestone should be paired with at least one delivery/operations improvement
- Stage B tasks should use `stage-b-*` naming
- task stacks should keep Research primary without dropping the parallel reliability and delivery tracks

## Success Criteria

Stage B is successful when:

- `Research Assistant` gains a reusable workbench or asset lifecycle rather than only discrete task outputs
- the runtime gains clearer recovery and control semantics for long-running work
- staging rehearsal becomes more repeatable and operator-oriented without pretending to be full production operations
- the repository is ready to decide whether to broaden scenario depth beyond Research or continue productizing Research further

## Next Step

Execute `tasks/stage-b-08-release-evidence-and-rehearsal-records.md` as the next active task of the second Stage B wave.

## First Task Wave

The first executable Stage B wave is complete:

- `tasks/archive/stage-b/stage-b-02-research-workbench-and-asset-lifecycle.md` (complete)
- `tasks/archive/stage-b/stage-b-03-recoverable-runtime-and-control-actions.md` (complete)
- `tasks/archive/stage-b/stage-b-04-staging-rehearsal-automation-and-handoff.md` (complete)

This wave kept `Research` as the primary Stage B track while pairing it with the first recovery-oriented runtime and
operator-oriented staging improvements.

## Second Task Wave

The second executable Stage B wave is now active:

- `tasks/archive/stage-b/stage-b-06-research-briefs-and-asset-comparison.md` (complete)
- `tasks/archive/stage-b/stage-b-07-runtime-recovery-history-and-operator-visibility.md` (complete)
- `tasks/stage-b-08-release-evidence-and-rehearsal-records.md` (active)

This wave keeps `Research` as the primary Stage B track while deepening the asset workflow, making runtime recovery
history more operator-visible, and capturing more durable release evidence around the staging rehearsal path.
