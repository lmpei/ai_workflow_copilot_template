# Task: stage-c-06-canonical-module-contracts-and-terminology

## Goal

Create one canonical module identity and scenario contract vocabulary across backend and frontend as part of the global
governance baseline initiated during Stage C early execution.

## Project Stage

- Stage: Stage C
- Track: Platform Reliability

## Why

The repository currently carries duplicated truth sources for module identity, task-state language, and scenario input
fields. That drift makes every cross-module change harder to implement and review because contracts look shared while
meaning different things in different layers. This task is global in effect even though it is being executed under a
Stage C task identifier.

## Context

Relevant documents:

- `docs/prd/STAGE_C_PLAN.md`
- `docs/review/STAGE_C_GOVERNANCE_DIAGNOSIS.md`
- `docs/PROJECT_GUIDE.md`

Typical code areas:

- `server/app/models/workspace.py`
- `server/app/schemas/workspace.py`
- `server/app/schemas/task.py`
- `server/app/schemas/scenario.py`
- `web/lib/types.ts`
- `web/lib/job-types.ts`

## Flow Alignment

- Flow A / B / C / D: applies to Research, Support, and Job task creation and inspection flows
- Related APIs: workspace, task, and eval contracts as needed
- Related schema or storage changes: allowed where needed to establish canonical module and contract vocabulary

## Dependencies

- Prior task: `tasks/archive/stage-c/stage-c-05-governance-convergence-planning.md`
- Blockers: none

## Scope

Allowed files:

- `server/app/models/`
- `server/app/schemas/`
- `server/app/services/`
- `web/lib/`
- `web/components/`
- `server/tests/`
- `docs/`
- `STATUS.md`

Disallowed files:

- module product renames
- unrelated deployment or infrastructure changes

## Deliverables

- Code or contract changes:
  - unify canonical module identity fields
  - converge scenario task selector terminology
  - define explicit scenario input and result view models instead of raw JSON-first contracts
- Docs changes:
  - document canonical field names and lifecycle terms

## Acceptance Criteria

- the repository has one canonical way to identify a module across storage, API, and UI
- scenario input vocabulary is explicit instead of drifting across multiple aliases
- task and eval success-state language is consistent across contracts and UI
- frontend code no longer depends on ambiguous type aliases that hide domain differences

## Verification Commands

- Backend:
  - `cd server`
  - `..\\.venv\\Scripts\\python.exe -m pytest tests`
- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - a collaborator can trace one canonical module field and one canonical scenario input field through backend and frontend
- Edge case:
  - backward-compatible data loading still works for persisted records that predate the cleanup
- Error case:
  - the cleanup should not leave both old and new canonical fields equally authoritative

## Risks

- trying to normalize every legacy alias in one pass could create a large migration surface

## Rollback Plan

- revert the contract and terminology cleanup while keeping the governance diagnosis and queued follow-up tasks intact
