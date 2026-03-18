# Stage A Plan

## Stage Name

`Stage A: Research Deepening With Trust Baseline`

## Status

- Status: complete
- Opened At: 2026-03-18
- Closed At: 2026-03-18

## Position In The Project

Stage A begins after the Phase 5 baseline. Phase 5 established the shared platform core plus visible scenario modules.
Stage A shifts the project from broad capability coverage toward deeper product value, stronger engineering trust, and
minimum delivery discipline.

## Planning Model

Stage A operates under the three-track roadmap model:

1. `Research`
2. `Platform Reliability`
3. `Delivery and Operations`

The tracks are parallel, but not equally weighted. Stage A prioritizes `Research` while requiring minimum progress in
the other two tracks.

## Priority Model

- Primary track:
  - `Research`
- Required parallel tracks:
  - `Platform Reliability`
  - `Delivery and Operations`

Stage A should not ship surface-level Research growth without also improving runtime trust and delivery discipline.

## Stage Goal

Make `Research Assistant` the first scenario module with real workflow depth while establishing the minimum reliability
and delivery baseline needed to support that depth.

## Track 1: Research

### Objective

Move `Research Assistant` from a runnable MVP to a reusable research workflow.

### Focus Areas

- structured research task inputs
- stronger evidence organization
- stable report/result structure
- iterative research continuation
- clearer separation of quick summaries versus formal research outputs

### Expected Outcomes

- users can run multi-step or multi-iteration research on one topic
- outputs are structured, not just freeform answers
- major findings remain traceable to sources
- at least one formal research-report path is stable enough to demonstrate repeatedly

## Track 2: Platform Reliability

### Objective

Establish a trustworthy baseline for the shared platform while Research grows deeper.

### Focus Areas

- consistent failure classification
- idempotency and duplicate-execution protection
- clearer state-machine boundaries
- minimum regression evaluation for Research
- stronger trace completeness for research-oriented workflows
- basic trust signals around grounded versus weakly supported answers

### Expected Outcomes

- failures on core paths are easier to diagnose
- repeated execution does not silently corrupt state
- Research changes can be checked against a minimum regression set
- traces are useful for debugging and quality review

## Track 3: Delivery and Operations

### Objective

Establish the minimum discipline required to move beyond a purely local-development system.

### Focus Areas

- local/dev/staging environment definitions
- secret and config handling rules
- migration and rollback rules
- release checklist
- minimum operator runbook
- a clear path toward a staging-grade deployment model

### Expected Outcomes

- collaborators can follow documented delivery rules
- migration and rollback are no longer implicit knowledge
- the system has a defined path from local-only execution toward staging

## Non-Goals

Stage A does not primarily optimize for:

- deep productization of Support Copilot
- deep productization of Job Assistant
- heavy multi-agent orchestration
- full checkpoint/resume infrastructure
- production-grade SRE or Kubernetes-scale operations
- renaming the three scenario modules

## Execution Rules

- every meaningful Research milestone should pull at least one `Platform Reliability` improvement with it
- every larger Research capability group should be paired with at least one `Delivery and Operations` improvement
- Stage A tasks should use `stage-a-*` naming
- task stacks should reflect the three-track model explicitly rather than treating reliability or delivery work as
  optional cleanup

## Success Criteria

Stage A is successful when:

- `Research Assistant` becomes the first clearly deepened module
- the platform gains a real trust baseline rather than relying on happy-path execution
- delivery and release discipline become documented and repeatable
- future Support/Job work can build on stronger shared primitives instead of on fragile scaffolding

## Next Step

Stage A is complete. The next formal planning unit is `Stage B: Research Workflow Productization With Recoverable Runtime`,
documented in `docs/prd/STAGE_B_PLAN.md`.

## Initial Task Wave

The first executable Stage A wave is:

- `tasks/archive/stage-a/stage-a-02-research-contracts-and-structured-results.md`
- `tasks/archive/stage-a/stage-a-03-research-report-assembly-and-surface.md`
- `tasks/archive/stage-a/stage-a-04-research-trust-and-regression-baseline.md`
- `tasks/archive/stage-a/stage-a-05-delivery-and-operations-baseline.md`

This wave keeps `Research` as the primary track while ensuring the first parallel work exists for `Platform Reliability`
and `Delivery and Operations`.

Completed planning and historical Phase 5 task specs should be archived so the root `tasks/` directory stays focused on
active Stage A execution work.

## Second Task Wave

The second executable Stage A wave is:

- `tasks/archive/stage-a/stage-a-07-research-iteration-workflow.md`
- `tasks/archive/stage-a/stage-a-08-research-eval-baseline.md`
- `tasks/archive/stage-a/stage-a-09-staging-delivery-path.md`

This wave keeps `Research` as the primary track, but shifts the work from baseline establishment toward iterative
Research workflow depth, explicit Research regression coverage, and a more concrete staging path.

## Closeout

Stage A closed after both execution waves completed:

- `tasks/archive/stage-a/stage-a-02-research-contracts-and-structured-results.md`
- `tasks/archive/stage-a/stage-a-03-research-report-assembly-and-surface.md`
- `tasks/archive/stage-a/stage-a-04-research-trust-and-regression-baseline.md`
- `tasks/archive/stage-a/stage-a-05-delivery-and-operations-baseline.md`
- `tasks/archive/stage-a/stage-a-07-research-iteration-workflow.md`
- `tasks/archive/stage-a/stage-a-08-research-eval-baseline.md`
- `tasks/archive/stage-a/stage-a-09-staging-delivery-path.md`

These tasks satisfied the Stage A goal of deepening Research while establishing a trust baseline and a minimum staging
delivery path.
