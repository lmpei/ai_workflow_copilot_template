# Task: Auth Overlay Visual Tightening

## Goal

Tighten the homepage-mounted auth overlay so it reads like a focused product entry layer instead of a generic centered login card.

## Project Phase

- Phase: Post-Stage-K bounded follow-through
- Scenario module: shared platform

## Why

The homepage auth overlay is functionally correct, but the current visual treatment still feels like a leftover form card. The entry layer needs cleaner hierarchy, fewer redundant words, and stronger field readability.

## Context

Relevant modules, dependencies, and related specs:

- `web/components/auth/auth-entry-overlay.tsx`
- `web/components/workspace/workspace-center-panel.tsx`
- `web/app/page.tsx`

## Flow Alignment

- Flow A:
  - unauthenticated user lands on the homepage with auth overlay open
- Flow B:
  - background home remains visible but inactive
- Flow C:
  - one focused entry layer presents only account, password, and the primary action
- Related APIs:
  - `POST /auth/enter`
- Related schema or storage changes:
  - none

## Dependencies

- Prior task:
  - `tasks/archive/home-auth-overlay-entry.md`
- Blockers:
  - none inside the repo

## Scope

Allowed files:

- `web/components/auth/`
- `web/components/workspace/`
- control-plane docs

Disallowed files:

- backend auth behavior
- deployment and environment files

## Deliverables

- Code changes:
  - visual refinement for the homepage auth overlay
- Test changes:
  - frontend verify pass
- Docs changes:
  - update `STATUS.md` after completion

## Acceptance Criteria

- Works correctly
- Tests pass
- Lint passes
- Type checks pass
- Build impact is addressed
- overlay copy is reduced to brand plus fields plus one primary action

## Verification Commands

- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - overlay still authenticates and returns to `next`
- Edge case:
  - auth error renders cleanly inside the new layout
- Error case:
  - build remains green after the visual refactor

## Risks

- visual tightening can accidentally reduce field affordance

## Rollback Plan

- restore the previous overlay component styling
