# Task: Stage F Summoned Supporting Surfaces And Operator Affordances

## Goal

Turn secondary detail such as document lists, execution detail, and analytics into lighter summoned surfaces that do
not compete with the main workbench.

## Project Phase

- Phase: Phase 5 follow-up
- Scenario module: cross-module

## Why

Even after the workbench becomes conversation-first, the product still needs honest access to document context,
execution detail, and analytics. Those surfaces should remain available, but only when the user asks for them.

## Context

Relevant surfaces:

- `web/components/workspace/workspace-workbench-panel.tsx`
- `web/app/workspaces/[workspaceId]/analytics/page.tsx`
- supporting drawers, sheets, or lightweight panels introduced during Stage F

## Flow Alignment

- Flow A / B / C / D:
  - main workbench -> summon supporting detail -> return to main work
- Related APIs:
  - analytics and task-status APIs only as existing readers
- Related schema or storage changes:
  - none

## Dependencies

- Prior task:
  - `tasks/archive/stage-f/stage-f-14-conversation-first-workbench-rebuild.md`
- Blockers:
  - none

## Scope

Allowed files:

- `web/app/workspaces/[workspaceId]/**`
- `web/components/workspace/*`
- `web/components/documents/*`
- related control-plane docs

Disallowed files:

- backend behavior changes unrelated to current UI contracts
- deployment/env files

## Deliverables

- Code changes:
  - lighter summoned supporting surfaces
  - analytics available by explicit affordance rather than page-level emphasis
  - clearer operator / advanced detail access without product clutter
- Test changes:
  - none required unless component contracts change
- Docs changes:
  - Stage F control-plane updates

## Acceptance Criteria

- analytics and deeper detail do not compete with the main workbench by default
- advanced detail is still honestly accessible
- the UI makes it clear when the user is opening secondary detail instead of the primary work surface

## Verification Commands

- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - user can open and close supporting detail without losing place
- Edge case:
  - compatibility routes still land in the correct summoned surface when required
- Error case:
  - no dead-end drawer or hidden state trap

## Risks

- losing honest operator visibility while simplifying
- leaving too much route and component duplication behind

## Rollback Plan

- revert the supporting-surface front-end files only
