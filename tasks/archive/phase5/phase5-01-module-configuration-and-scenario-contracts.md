# Task: phase5-01-module-configuration-and-scenario-contracts

## Goal

Establish the shared scenario-module contracts so Phase 5 modules build on platform primitives instead of forking the platform.

## Project Phase

- Phase: Phase 5
- Scenario module: shared scenario foundation

## Why

Phase 5 should prove that job, support, and research flows can be expressed as reusable module configurations, task types, and result contracts on top of the existing platform core.

## Context

Phase 4 already delivered documents, retrieval, tasks, agents, evals, and observability. Phase 5 should add scenario semantics without replacing the existing workspace, task, trace, or eval models.

## Flow Alignment

- Flow A / B / C / D: Flow B / C / D
- Related APIs: workspaces, tasks, agents, evals
- Related schema or storage changes: module type, module config, module-specific task/result contracts

## Dependencies

- Prior task:
  - `phase4-08-docs-and-handoff`
- Blockers: none

## Scope

Allowed files:

- `server/app/models/`
- `server/app/schemas/`
- `server/app/repositories/`
- `server/app/services/`
- `server/alembic/`
- `server/tests/`
- `web/lib/`

Disallowed files:

- `server/app/workers/`
- `server/app/agents/`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`

## Deliverables

- Code changes:
  - Add module-level configuration and contract primitives
  - Define shared scenario task and result types
- Test changes:
  - Add repository/service coverage for module config behavior
- Docs changes:
  - None required in this task

## Acceptance Criteria

- Job, support, and research modules can be represented through shared platform contracts
- Existing platform primitives remain the source of truth
- Tests pass
- Lint passes
- Type checks pass

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python -m ruff check .`
  - `..\.venv\Scripts\python -m mypy app`
  - `..\.venv\Scripts\python -m pytest`
- Frontend:
  - None required unless shared client types change

## Tests

- Normal case: a workspace can be associated with a supported module type and config
- Edge case: missing optional module config still keeps defaults valid
- Error case: unsupported module type is rejected

## Risks

- Over-specializing data models here would undo the platform-first architecture

## Rollback Plan

- Revert the module contract additions while keeping existing platform primitives unchanged
