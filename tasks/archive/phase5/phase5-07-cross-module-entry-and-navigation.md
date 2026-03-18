# Task: phase5-07-cross-module-entry-and-navigation

## Goal

Add the minimum cross-module navigation and entry surfaces so users can discover and switch between scenario modules cleanly.

## Project Phase

- Phase: Phase 5
- Scenario module: shared module UX

## Why

Once multiple scenario modules exist, the product needs a consistent way to enter them without turning workspaces into disconnected one-off pages.

## Context

This task should focus on module discovery, entry points, and shared layout patterns, not on building a full portal or admin console.

## Flow Alignment

- Flow A / B / C / D: Flow B / C / D
- Related APIs: module metadata, tasks, analytics
- Related schema or storage changes: none beyond module config contracts

## Dependencies

- Prior task:
  - `phase5-03-research-assistant-frontend-surface`
  - `phase5-04-support-copilot-skeleton`
  - `phase5-05-job-assistant-skeleton`
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
  - Add shared module entry/navigation UI
  - Keep scenario pages discoverable and consistent
- Test changes:
  - Continue using frontend verify/build path
- Docs changes:
  - None required in this task

## Acceptance Criteria

- Users can discover research, support, and job module surfaces from shared navigation
- Navigation does not bypass workspace scope or shared platform pages
- Frontend verify/build passes

## Verification Commands

- Backend:
  - None required in this task
- Frontend:
  - `cd web`
  - `npm.cmd run verify`

## Tests

- Normal case: users can navigate from a workspace into each available module
- Edge case: modules that are not configured yet render a clear placeholder state
- Error case: invalid module route shows a safe empty/error state

## Risks

- A heavyweight dashboard here would expand scope beyond the minimum Phase 5 navigation surface

## Rollback Plan

- Revert cross-module navigation additions while preserving individual module pages
