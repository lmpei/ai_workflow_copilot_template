# Stage C Plan

## Stage Name

`Stage C: Multi-Module Workflow Expansion With Cross-Module Readiness`

## Status

- Status: active
- Opened At: 2026-03-21
- First Task Wave: active

## Position In The Project

Stage C begins after the formal closeout of Stage B. Stage B turned Research into a reusable workflow surface, exposed
recoverable runtime controls, and added operator-facing rehearsal evidence. Stage C uses that stronger baseline to
prove the shared platform can carry deeper non-Research workflows without splitting architecture, runtime behavior, or
delivery discipline.

## Planning Model

Stage C operates under the same three-track roadmap model:

1. `Research`
2. `Platform Reliability`
3. `Delivery and Operations`

The tracks remain parallel, but Stage C uses the mature Research flow as a reference pattern while broadening workflow
depth into the other scenario modules.

## Priority Model

- Primary track:
  - `Research` as the reference workflow for broader scenario-module depth
- Required parallel tracks:
  - `Platform Reliability`
  - `Delivery and Operations`

Stage C should not deepen Support Copilot or Job Assistant in ways that bypass the shared runtime, eval, or delivery
contracts already established by the platform core.

## Stage Goal

Prove that the shared platform core can support more than one deep workflow surface by lifting Support Copilot and Job
Assistant closer to Research-level structure while making cross-module quality and demo readiness explicit.

## Track 1: Research

### Objective

Use the mature Research workflow as the reference pattern while extending comparable structured workflow depth into
Support Copilot and Job Assistant.

### Focus Areas

- stronger Support Copilot task inputs, grounded outputs, and case-handling surfaces
- stronger Job Assistant task inputs, structured match outputs, and hiring-workflow surfaces
- shared module-shape consistency across structured input, structured result, and operator inspection paths
- reusable module patterns that do not fork the shared platform core

### Expected Outcomes

- Support Copilot is no longer only a runnable skeleton and becomes a clearer grounded case workflow
- Job Assistant is no longer only a runnable skeleton and becomes a clearer structured hiring workflow
- the platform can demonstrate deeper workflow value in more than one scenario module

## Track 2: Platform Reliability

### Objective

Make cross-module quality and operator expectations more consistent as scenario depth expands beyond Research.

### Focus Areas

- cross-module eval and quality-baseline alignment
- contract consistency across Research, Support, and Job task/result shapes
- clearer operator expectations for inspecting module outputs and failures
- runtime and test coverage that catches drift between scenario modules

### Expected Outcomes

- Support and Job workflow additions are checked against shared quality expectations rather than added as isolated UI features
- cross-module operator inspection becomes more predictable
- the platform is better positioned to compare scenario depth without inventing separate reliability rules for each module

## Track 3: Delivery and Operations

### Objective

Turn the Stage B release routine into a cross-module demo and release-readiness path.

### Focus Areas

- cross-module demo checklist and release-candidate expectations
- staging and rehearsal expectations that cover all three scenario modules instead of Research alone
- clearer capture of which scenario surfaces were validated in a release-like rehearsal
- lightweight but durable evidence for broader module readiness

### Expected Outcomes

- a collaborator can rehearse and hand off a candidate that exercises Research, Support, and Job surfaces together
- release evidence becomes more useful for cross-module demos without pretending to be production operations
- Stage C delivery discipline scales with broader platform coverage

## Non-Goals

Stage C does not primarily optimize for:

- renaming the three module products
- full production-grade SRE or Kubernetes-scale operations
- durable multi-agent orchestration beyond the current workflow model
- deep human approval workflows
- brand-new scenario modules beyond Research, Support, and Job

## Execution Rules

- Stage C tasks should use `stage-c-*` naming
- Stage C should deepen Support and Job through shared platform primitives rather than special-case forks
- every module-depth increment should be paired with a cross-module quality or delivery increment
- Research should remain the reference implementation, not the only module with durable workflow depth

## Success Criteria

Stage C is successful when:

- Support Copilot and Job Assistant become clearly demoable structured workflows rather than only runnable skeletons
- cross-module quality and operator inspection rules are more consistent across Research, Support, and Job
- the release/demo path can explicitly show readiness across all three scenario modules
- the repository is ready to decide whether to continue broadening scenario depth or shift toward stronger external delivery readiness

## Next Step

Execute `tasks/stage-c-02-support-copilot-grounded-case-workflow.md` as the next active task of the first Stage C wave.

## First Task Wave

The first executable Stage C wave is now active:

- `tasks/stage-c-02-support-copilot-grounded-case-workflow.md` (active)
- `tasks/stage-c-03-job-assistant-structured-hiring-workflow.md` (active)
- `tasks/stage-c-04-cross-module-quality-and-demo-readiness.md` (active)

This wave uses the mature Research workflow as the reference pattern while deepening Support and Job and tightening the
cross-module quality and delivery path.

## Global Governance Baseline Initiated During Stage C Early Execution

Alongside the Stage C task waves, the repository now also carries a global governance baseline that was identified and
formalized during Stage C early execution. This baseline is global rather than Stage C-specific because it addresses
cross-cutting contract, boundary, runtime, and maintainability issues that affect the whole repository.

The governance diagnosis is recorded in:

- `docs/review/STAGE_C_GOVERNANCE_DIAGNOSIS.md`

The planning task that initiated this baseline is archived as:

- `tasks/archive/stage-c/stage-c-05-governance-convergence-planning.md`

## Global Governance Baseline Workstreams

The global governance baseline was completed on 2026-03-22 through these archived Stage C task identifiers:

- `tasks/archive/stage-c/stage-c-06-canonical-module-contracts-and-terminology.md`
- `tasks/archive/stage-c/stage-c-07-scenario-registry-and-boundary-hardening.md`
- `tasks/archive/stage-c/stage-c-08-runtime-architecture-alignment.md`
- `tasks/archive/stage-c/stage-c-09-maintainability-annotations-and-surface-hygiene.md`

## Readiness Gate After Stage C

This baseline no longer blocks the remaining Stage C task wave. The planning unit that follows Stage C should still
confirm these governance guarantees remain intact before opening.
