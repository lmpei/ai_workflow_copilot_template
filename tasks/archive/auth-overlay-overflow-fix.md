# Task: Auth Overlay Overflow Fix

## Goal

Fix the auth overlay form field overflow so the account and password inputs stay fully inside the overlay bounds.

## Project Phase

- Phase: Post-Stage-K bounded follow-through
- Scenario module: shared platform

## Why

The homepage auth overlay is now the primary product-facing auth gate. Field overflow breaks the visual integrity of the entry layer and makes the experience feel unfinished.

## Context

Relevant modules, dependencies, and related specs:

- `web/components/auth/auth-entry-overlay.tsx`

## Flow Alignment

- Flow A:
  - unauthenticated user opens the homepage auth overlay
- Flow B:
  - account and password fields must stay inside the overlay frame on common desktop widths
- Related APIs:
  - none
- Related schema or storage changes:
  - none

## Dependencies

- Prior task:
  - `tasks/archive/auth-overlay-visual-tightening.md`
- Blockers:
  - none inside the repo

## Scope

Allowed files:

- `web/components/auth/`
- control-plane docs

Disallowed files:

- backend auth behavior
- deployment and environment files

## Deliverables

- Code changes:
  - overflow fix for auth overlay field sizing
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
- auth overlay fields and primary action remain inside the overlay boundary

## Verification Commands

- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - account and password inputs render inside the overlay frame
- Edge case:
  - long account text still stays inside the field and overlay width
- Error case:
  - build remains green after the layout fix

## Risks

- tightening the box model can slightly change spacing and require small visual follow-up

## Rollback Plan

- restore the previous overlay field sizing
