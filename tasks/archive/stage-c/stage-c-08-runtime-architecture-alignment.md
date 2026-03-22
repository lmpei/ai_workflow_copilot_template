# Task: stage-c-08-runtime-architecture-alignment

## Goal

Refactor the shared execution path so scenario orchestration, runtime-control semantics, and Research-specific
extensions have clear boundaries as part of the global governance baseline initiated during Stage C early execution.

## Project Stage

- Stage: Stage C
- Track: Platform Reliability

## Why

The current executor mixes generic runtime concerns with Research-specific lineage, asset, and result behavior. At the
same time, task and eval control flows duplicate cancel and retry orchestration, and the scenario graphs are nearly the
same pipeline repeated three times. That is unstable architecture, not just local cleanup debt. This task is a global
runtime-alignment effort even though it is scheduled under Stage C.

## Context

Relevant documents:

- `docs/prd/STAGE_C_PLAN.md`
- `docs/review/STAGE_C_GOVERNANCE_DIAGNOSIS.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`

Typical code areas:

- `server/app/core/runtime_control.py`
- `server/app/services/task_service.py`
- `server/app/services/eval_service.py`
- `server/app/services/task_execution_service.py`
- `server/app/services/eval_execution_service.py`
- `server/app/services/research_assistant_service.py`
- `server/app/services/research_asset_service.py`
- `server/app/agents/graph.py`

## Flow Alignment

- Flow A / B / C / D: applies to task execution, eval execution, runtime recovery, and agent orchestration
- Related APIs: task and eval control endpoints, operator inspection surfaces as needed
- Related schema or storage changes: allowed only where runtime-control or execution extension points need explicit contracts

## Dependencies

- Prior task: `tasks/archive/stage-c/stage-c-05-governance-convergence-planning.md`
- Blockers:
  - `tasks/archive/stage-c/stage-c-06-canonical-module-contracts-and-terminology.md`
  - `tasks/archive/stage-c/stage-c-07-scenario-registry-and-boundary-hardening.md`

## Scope

Allowed files:

- `server/app/core/`
- `server/app/services/`
- `server/app/agents/`
- `server/app/schemas/`
- `server/tests/`
- `docs/`
- `web/components/` if operator inspection surfaces need contract alignment

Disallowed files:

- broad UI redesign unrelated to runtime inspection
- unrelated staging or deployment automation

## Deliverables

- Code or contract changes:
  - converge shared runtime-control behavior for tasks and evals
  - extract or clarify a shared scenario execution skeleton
  - move Research-only concerns behind explicit extension points
- Docs changes:
  - describe the intended shared executor boundary and extension model

## Acceptance Criteria

- task and eval cancel or retry behavior share the same conceptual runtime-control model
- scenario graph behavior no longer relies on near-duplicate pipelines without an explicit shared skeleton
- Research-specific lineage, asset sync, or trust behavior no longer appears as an implicit default in generic executor code
- operator-visible contracts remain honest about supported recovery semantics

## Verification Commands

- Backend:
  - `cd server`
  - `..\\.venv\\Scripts\\python.exe -m pytest tests`
- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - task and eval recovery actions produce aligned state transitions and operator-visible details
- Edge case:
  - Research extensions still work without forcing Support and Job down Research-only branches
- Error case:
  - executor cleanup should not imply unsupported checkpoint or resume behavior

## Risks

- runtime refactors can create regressions across async execution, traces, and operator surfaces if the new extension points are underspecified

## Rollback Plan

- restore the current executor wiring while keeping the governance diagnosis and boundary decisions recorded
