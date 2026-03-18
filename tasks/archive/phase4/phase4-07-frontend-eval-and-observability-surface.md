# Task: phase4-07-frontend-eval-and-observability-surface

## Goal

Add the minimum frontend UI for evaluation datasets, eval runs, and richer observability summaries.

## Project Phase

- Phase: Phase 4
- Scenario module: shared platform core

## Why

Phase 4 should be demoable from the product surface, not only through backend APIs and worker logs.

## Context

The frontend already supports auth, documents, chat, tasks, and analytics. This task should extend those surfaces with minimal eval and observability views.

## Flow Alignment

- Flow A / B / C / D: Flow D
- Related APIs: eval dataset/run APIs and Phase 4 analytics endpoints
- Related schema or storage changes: none beyond API contracts

## Dependencies

- Prior task:
  - `phase4-03-eval-api-surface`
  - `phase4-04-eval-runner-and-worker-execution`
  - `phase4-06-analytics-and-observability-surface`
- Blockers: none

## Scope

Allowed files:

- `web/app/`
- `web/components/`
- `web/lib/`

Disallowed files:

- `server/`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`

## Deliverables

- Code changes:
  - Add minimal UI for creating/viewing eval datasets and runs
  - Show summary cards and per-case results
  - Extend analytics UI with Phase 4 observability summaries
- Test changes:
  - Continue using frontend verify/build path; no new framework required
- Docs changes:
  - None required in this task

## Acceptance Criteria

- Users can create or launch eval runs from the frontend
- Users can inspect run status and per-case outcomes
- Analytics UI can show Phase 4 summary metrics
- Frontend build/verify passes

## Verification Commands

- Backend:
  - None required for this task beyond depending on already-working APIs
- Frontend:
  - `cd web`
  - `npm.cmd run verify`

## Tests

- Normal case: create eval run and view completed results
- Edge case: empty datasets and empty analytics states render clearly
- Error case: failed eval run surfaces a useful error state in UI

## Risks

- Trying to build a full BI dashboard here would expand scope beyond Phase 4

## Rollback Plan

- Revert frontend eval/analytics additions while preserving backend APIs
