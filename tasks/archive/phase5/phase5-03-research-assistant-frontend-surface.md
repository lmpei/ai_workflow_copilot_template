# Task: phase5-03-research-assistant-frontend-surface

## Goal

Add the minimum frontend UI needed to demo the Research Assistant module end to end.

## Project Phase

- Phase: Phase 5
- Scenario module: research

## Why

Phase 5 should be visible from the product surface, not only through backend task execution and raw JSON results.

## Context

This task should build on the Research Assistant backend MVP and reuse the current workspaces, documents, chat, tasks, and analytics navigation patterns.

## Flow Alignment

- Flow A / B / C / D: Flow B / C / D
- Related APIs: research module APIs, tasks, evals, analytics
- Related schema or storage changes: none beyond API contracts

## Dependencies

- Prior task:
  - `phase5-02-research-assistant-backend-mvp`
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
  - Add a minimal Research Assistant UI flow
  - Show task inputs, structured outputs, and linked evidence
- Test changes:
  - Continue using frontend verify/build path
- Docs changes:
  - None required in this task

## Acceptance Criteria

- Users can launch the Research Assistant flow from the frontend
- Users can inspect the resulting structured output and evidence
- Frontend verify/build passes

## Verification Commands

- Backend:
  - None required beyond already-working APIs
- Frontend:
  - `cd web`
  - `npm.cmd run verify`

## Tests

- Normal case: research module flow renders a completed task result
- Edge case: limited document context still renders a stable empty-state result
- Error case: failed research task surfaces a clear message in UI

## Risks

- Building a bespoke dashboard here would expand scope beyond the MVP module surface

## Rollback Plan

- Revert the research-specific frontend additions while preserving shared task and analytics pages
