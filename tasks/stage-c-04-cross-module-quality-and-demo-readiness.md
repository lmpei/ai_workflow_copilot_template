# Task: stage-c-04-cross-module-quality-and-demo-readiness

## Goal

Define and implement the minimum cross-module quality and demo-readiness path for Research, Support, and Job.

## Project Stage

- Stage: Stage C
- Track: Platform Reliability and Delivery and Operations

## Why

If Support and Job become deeper workflows, the platform needs a clearer shared standard for how those workflows are
checked, demonstrated, and handed off. Stage C should not let module depth expand faster than cross-module quality and
delivery readiness.

## Context

Relevant documents:

- `docs/prd/STAGE_C_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `docs/PROJECT_GUIDE.md`
- `docs/development/DELIVERY_BASELINE.md`
- `docs/development/STAGING_RELEASE_PATH.md`
- `web/components/evals/`

## Flow Alignment

- Flow A / B / C / D: applies to all scenario-module flows
- Related APIs: eval and task inspection surfaces as needed
- Related schema or storage changes: none unless shared quality recording needs a contract update

## Dependencies

- Prior task: `tasks/archive/stage-c/stage-c-01-task-stack-planning.md`
- Blockers: none

## Scope

Allowed files:

- `server/app/services/` and `server/app/schemas/` if cross-module quality contracts need tightening
- `server/tests/`
- `web/components/evals/`
- `web/components/workspace/` if cross-module demo guidance needs surfacing
- `web/lib/`
- `docs/development/`
- `docs/PROJECT_GUIDE.md`
- `README.md`
- `STATUS.md`

Disallowed files:

- unrelated module-name changes
- heavyweight production-operations automation beyond current project maturity

## Deliverables

- Code or contract changes:
  - add only the minimum shared quality or inspection support needed for cross-module readiness
- Docs changes:
  - define a cross-module demo/release-readiness baseline that explicitly covers Research, Support, and Job

## Acceptance Criteria

- a collaborator can point to a shared readiness path that covers all three module surfaces
- cross-module quality expectations are clearer than ad hoc manual checking
- the resulting routine still stays lightweight and does not overstate production maturity

## Verification Commands

- Backend:
  - `cd server`
  - `..\\.venv\\Scripts\\python.exe -m pytest tests`
- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - a collaborator can verify a release/demo candidate across Research, Support, and Job without relying on hidden knowledge
- Edge case:
  - modules with thinner context still surface honest degraded outputs within the shared demo path
- Error case:
  - the quality/demo readiness path does not claim stronger operational guarantees than the project actually implements

## Risks

- trying to formalize cross-module readiness too heavily could create premature process overhead before the workflows themselves are deep enough

## Rollback Plan

- revert the cross-module readiness additions while keeping Stage C active for scenario workflow work