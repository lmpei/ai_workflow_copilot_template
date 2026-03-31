# Task: Stage F Personal Homepage And Project Home Viewport Reset

## Goal

Make the root personal homepage and the `/app` project home fit their primary story and actions inside one clearer,
denser first viewport.

## Project Phase

- Phase: Phase 5 follow-up
- Scenario module: cross-module

## Why

The current surfaces still feel too verbose and too single-column. The user should not need long scrolling or abstract
copy to understand who the site owner is, which project to open, or how to continue work inside this specific
project.

## Context

Relevant surfaces:

- `web/app/page.tsx`
- `web/app/app/page.tsx`
- `web/components/workspace/workspace-center-panel.tsx`

Related product choices:

- the root site is the personal homepage
- the project-facing home is also the workspace center for this project
- guided demo remains a lightweight entry
- existing workspaces stay bounded inside one fixed-height scroll region

## Flow Alignment

- Flow A / B / C / D:
  - root personal-homepage path
  - project-home / workspace-center path
- Related APIs:
  - existing workspace list and public-demo settings APIs only
- Related schema or storage changes:
  - none

## Dependencies

- Prior task:
  - `tasks/archive/stage-f/stage-f-12-wave-three-replanning.md`
- Blockers:
  - none

## Scope

Allowed files:

- `web/app/page.tsx`
- `web/app/app/page.tsx`
- `web/components/workspace/workspace-center-panel.tsx`
- `web/components/ui/*`
- related control-plane docs

Disallowed files:

- `server/`
- auth/provider/deployment files

## Deliverables

- Code changes:
  - denser root personal homepage
  - denser `/app` project home / workspace center
  - lighter copy and stronger action hierarchy
- Test changes:
  - none required unless a component contract changes
- Docs changes:
  - Stage F control-plane updates

## Acceptance Criteria

- the root homepage reads like a personal site, not a product console
- the project home reads like one clear product start page
- the first viewport communicates the primary story and actions without long explanatory stacks
- existing workspaces remain bounded in one scroll region

## Verification Commands

- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - first-time visitor understands what the site is and where to enter the project
- Edge case:
  - many existing workspaces do not expand the whole page without bound
- Error case:
  - project-home and personal-home responsibilities do not overlap again

## Risks

- over-compressing content until the site becomes vague
- preserving too much old copy and hierarchy because it already exists

## Rollback Plan

- revert the affected root/project-home files only
