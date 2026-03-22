# Task: stage-c-09-maintainability-annotations-and-surface-hygiene

## Goal

Add the documentation, comments, and surface cleanup needed so the repository's visible structure better matches the
real architecture as part of the global governance baseline initiated during Stage C early execution.

## Project Stage

- Stage: Stage C
- Track: Delivery and Operations

## Why

Part of the current governance risk comes from undocumented behavior and misleading surface names, not only from code
structure. A collaborator can still misread stub workers, placeholder agent routes, or legacy frontend names as active
product boundaries. That makes maintenance and future planning harder than it should be. This is a global
maintainability task, not only a Stage C local polish pass.

## Context

Relevant documents:

- `docs/review/STAGE_C_GOVERNANCE_DIAGNOSIS.md`
- `docs/PROJECT_GUIDE.md`
- `ARCHITECTURE.md`

Typical code and doc areas:

- `server/app/core/runtime_control.py`
- `server/app/services/task_execution_service.py`
- `server/app/services/research_assistant_service.py`
- `server/app/services/research_asset_service.py`
- `server/app/agents/graph.py`
- `server/app/api/routes/agents.py`
- `server/app/workers/`
- `web/lib/navigation.ts`
- `web/components/tasks/task-manager.tsx`

## Flow Alignment

- Flow A / B / C / D: maintainability support for all scenario-module flows
- Related APIs: none required beyond honest documentation of current surfaces
- Related schema or storage changes: none unless comments or docs reveal a tiny missing contract field needed for clarity

## Dependencies

- Prior task: `tasks/archive/stage-c/stage-c-05-governance-convergence-planning.md`
- Blockers:
  - should follow the main contract and boundary cleanups closely enough that docs describe the intended architecture, not a soon-to-be-removed shape

## Scope

Allowed files:

- `docs/`
- `STATUS.md`
- `ARCHITECTURE.md`
- `server/app/core/`
- `server/app/services/`
- `server/app/agents/`
- `server/app/api/routes/`
- `server/app/workers/`
- `web/lib/`
- `web/components/`

Disallowed files:

- deep feature changes disguised as comment work
- module product renames without confirmation

## Deliverables

- Docs changes:
  - explain runtime-control semantics and scenario contract precedence
  - mark scaffold or placeholder surfaces honestly in control-plane or long-form docs
- Code comments:
  - add only the highest-value comments and docstrings in unstable or easy-to-misread orchestration code
- Surface cleanup:
  - rename or mark misleading internal surfaces where the payoff is immediate and low-risk

## Acceptance Criteria

- a collaborator can distinguish real runtime entrypoints from scaffold or placeholder surfaces
- the shared executor and runtime-control semantics are easier to understand without reading every call site
- frontend and backend surface names no longer imply cleaner or broader support than the implementation actually provides

## Verification Commands

- Repository:
  - manual doc consistency review
- Backend:
  - `cd server`
  - `..\\.venv\\Scripts\\python.exe -m pytest tests`
- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - a collaborator can navigate the repository and understand which surfaces are active, shared, scenario-specific, or placeholder
- Edge case:
  - comments and docs still describe the intended architecture after nearby contract cleanup lands
- Error case:
  - annotation work should not overstate product completeness or supported runtime behavior

## Risks

- documentation can drift quickly if it is written before the higher-priority contract and boundary tasks settle

## Rollback Plan

- revert the maintainability annotations and surface-hygiene changes without removing the governance diagnosis
