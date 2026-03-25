# Task: stage-c-14-cross-module-eval-coverage-and-rehearsal-evidence

## Goal

Turn the Stage C readiness baseline into more durable cross-module eval-coverage and rehearsal-evidence routines.

## Project Stage

- Stage: Stage C
- Track: Platform Reliability and Delivery and Operations

## Why

`stage-c-04` made the readiness baseline visible, but it still depends heavily on manual inspection. Stage C needs a
clearer way to show which module evals exist, which default tasks were checked, and how rehearsal evidence is recorded.

## Context

Relevant documents:

- `docs/prd/STAGE_C_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `docs/development/STAGE_C_CROSS_MODULE_READINESS.md`
- `docs/development/DELIVERY_BASELINE.md`
- `docs/development/STAGING_RELEASE_PATH.md`
- `web/components/evals/eval-manager.tsx`

## Flow Alignment

- Flow C / D: eval inspection, delivery evidence, and release-like rehearsal handling
- Related APIs: eval datasets, eval runs, scenario registry metadata
- Related schema or storage changes: none unless minimal shared coverage metadata needs a durable contract

## Dependencies

- Prior task: `tasks/archive/stage-c/stage-c-11-wave-two-planning.md`
- Blockers: none

## Scope

Allowed files:

- `server/app/services/` and `server/app/schemas/` only if minimal shared coverage data is required
- `server/tests/`
- `web/components/evals/`
- `web/lib/`
- `docs/development/`
- `docs/PROJECT_GUIDE.md`
- `README.md`
- `STATUS.md`
- `DECISIONS.md`

Disallowed files:

- heavyweight production-operations automation beyond the current project maturity
- unrelated scenario-specific workflow changes that belong in `stage-c-12` or `stage-c-13`

## Deliverables

- Code or contract changes:
  - add only the minimum shared eval-coverage or inspection support needed for cross-module evidence
- Docs changes:
  - define how cross-module rehearsal evidence should record module checks, default eval tasks, and known gaps
  - add or extend reusable evidence templates if needed

## Acceptance Criteria

- a collaborator can tell which default module evals exist or are still missing without relying on hidden project knowledge
- cross-module rehearsal evidence can be captured in one lightweight durable record
- the resulting routine stays lightweight and does not overstate production maturity

## Verification Commands

- Backend:
  - `cd server`
  - `..\\.venv\\Scripts\\python.exe -m pytest tests`
- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - a collaborator can inspect module eval coverage and rehearsal evidence across Research, Support, and Job
- Edge case:
  - missing eval coverage is made explicit instead of silently treated as complete readiness
- Error case:
  - the new evidence path does not imply stronger operational guarantees than the repository actually implements

## Risks

- trying to formalize cross-module evidence too heavily could create delivery-process overhead that outruns actual product depth

## Rollback Plan

- revert the cross-module evidence additions while preserving the Stage C readiness baseline from `stage-c-04`
