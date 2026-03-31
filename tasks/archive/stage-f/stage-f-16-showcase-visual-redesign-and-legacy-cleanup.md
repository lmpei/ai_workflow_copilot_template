# Task: Stage F Showcase Visual Redesign And Legacy Cleanup

## Goal

Apply one final visual redesign and cleanup pass after the new structure lands, including deletion of superseded legacy
front-end surfaces.

## Project Phase

- Phase: Phase 5 follow-up
- Scenario module: cross-module

## Why

The current front-end is constrained by inherited component shapes and leftover surfaces. The product should look
intentional enough for external showcase use, and the repo should stop carrying dead UI surfaces once the new shape is
stable.

## Context

Relevant surfaces:

- root personal homepage
- `/app` project home / workspace center
- main workbench and its supporting surfaces
- legacy front-end components no longer used after the third Stage F wave

## Flow Alignment

- Flow A / B / C / D:
  - polish the final user path after structure is stable
- Related APIs:
  - none beyond the existing front-end readers
- Related schema or storage changes:
  - none

## Dependencies

- Prior task:
  - `tasks/archive/stage-f/stage-f-15-summoned-supporting-surfaces-and-operator-affordances.md`
- Blockers:
  - none

## Scope

Allowed files:

- `web/app/**`
- `web/components/**`
- `web/lib/**`
- related control-plane docs

Disallowed files:

- backend runtime or schema changes
- deployment/env files

## Deliverables

- Code changes:
  - final visual-system pass on the redesigned surfaces
  - deletion of superseded legacy components and routes where safe
- Test changes:
  - none required unless contracts change
- Docs changes:
  - Stage F closeout or the next planning handoff

## Acceptance Criteria

- the redesigned surfaces feel consistent and intentional
- obviously dead legacy UI files are removed
- the product no longer depends on redundant explanation or leftover console-like layout

## Verification Commands

- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - the most common user path looks and feels coherent
- Edge case:
  - cleanup does not remove still-used components
- Error case:
  - no broken imports or routes after legacy cleanup

## Risks

- deleting a surface that still has one hidden entry path
- spending too much time on cosmetics before structure is stable

## Rollback Plan

- revert the visual-cleanup commit or affected front-end files only
