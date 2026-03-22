# Task: stage-c-07-scenario-registry-and-boundary-hardening

## Goal

Replace repeated scenario registry logic with one canonical registry and restore hard module boundaries in the service
and repository layers as part of the global governance baseline initiated during Stage C early execution.

## Project Stage

- Stage: Stage C
- Track: Platform Reliability

## Why

The current shared core behaves like a scenario switchboard. Module labels, entry task types, and dispatch rules are
duplicated across multiple backend and frontend surfaces, while service-layer contract logic has already leaked into the
repository layer. That shape will keep expanding the blast radius of every module change. This is a global boundary
repair task, not only a Stage C feature-support task.

## Context

Relevant documents:

- `docs/prd/STAGE_C_PLAN.md`
- `docs/review/STAGE_C_GOVERNANCE_DIAGNOSIS.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`

Typical code areas:

- `server/app/schemas/scenario.py`
- `server/app/services/task_service.py`
- `server/app/services/task_execution_service.py`
- `server/app/services/scenario_contract_service.py`
- `server/app/repositories/workspace_repository.py`
- `web/lib/navigation.ts`
- `web/components/evals/eval-manager.tsx`

## Flow Alignment

- Flow A / B / C / D: applies to module registration, task routing, and operator inspection flows
- Related APIs: workspace and task creation APIs, eval surfaces as needed
- Related schema or storage changes: only as needed to remove duplicated registry state and boundary leaks

## Dependencies

- Prior task: `tasks/archive/stage-c/stage-c-05-governance-convergence-planning.md`
- Blockers:
  - `tasks/stage-c-06-canonical-module-contracts-and-terminology.md` should define the canonical vocabulary first or in parallel

## Scope

Allowed files:

- `server/app/schemas/`
- `server/app/services/`
- `server/app/repositories/`
- `server/app/api/routes/`
- `server/app/agents/`
- `web/lib/`
- `web/components/`
- `server/tests/`
- `docs/`

Disallowed files:

- unrelated module-depth feature expansion
- heavyweight runtime redesign unrelated to registry and boundary repair

## Deliverables

- Code or contract changes:
  - add one canonical scenario registry
  - remove repeated scenario task-type lists from shared orchestration layers
  - move contract resolution out of repositories
  - stop cross-scenario fallback input guesses at module boundaries
- Docs changes:
  - document the registry ownership point and boundary rules

## Acceptance Criteria

- backend and frontend consume one canonical scenario registry or a derived artifact from one source
- repository code no longer depends on service-layer contract resolution
- Support and Job inputs are validated against their own canonical module contracts
- shared orchestration code no longer grows by repeated `if task_type in ...` scenario lists

## Verification Commands

- Backend:
  - `cd server`
  - `..\\.venv\\Scripts\\python.exe -m pytest tests`
- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - a new or updated scenario capability can be registered without editing scattered switchboard lists
- Edge case:
  - unsupported or malformed module input is rejected at the correct boundary instead of being guessed into another scenario
- Error case:
  - registry cleanup should not leave the UI and backend reading different scenario availability rules

## Risks

- moving registry ownership can surface hidden assumptions in existing UI and eval labels

## Rollback Plan

- restore the prior registry wiring while preserving the governance diagnosis and follow-up task stack
