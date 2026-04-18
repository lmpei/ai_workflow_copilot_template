# Task: Home Auth Overlay Entry

## Goal

Replace the standalone frontend auth page with one homepage-mounted auth overlay that keeps the product home visible as a blurred, non-interactive background.

## Project Phase

- Phase: Post-Stage-K bounded follow-through
- Scenario module: shared platform

## Why

The product home is already the visual entry to the system. Sending users into a separate login page breaks that experience and keeps an outdated auth surface alive. The auth entry should feel like one focused gate layered over the home, not a second product.

## Context

Relevant modules, dependencies, and related specs:

- `web/app/page.tsx`
- `web/components/workspace/workspace-center-panel.tsx`
- `web/components/auth/auth-required.tsx`
- `web/app/(auth)/login/page.tsx`
- `web/app/(auth)/register/page.tsx`
- `web/lib/auth.ts`

## Flow Alignment

- Flow A:
  - user opens auth entry from the product home or is redirected there from a protected path
- Flow B:
  - homepage remains visible as the background but becomes blurred and non-interactive
- Flow C:
  - one centered auth overlay handles account-plus-password entry
- Flow D:
  - successful auth restores the intended `next` path
- Related APIs:
  - existing `POST /auth/enter`
- Related schema or storage changes:
  - none

## Dependencies

- Prior task:
  - `tasks/archive/unified-auth-entry.md`
- Blockers:
  - none inside the repo

## Scope

Allowed files:

- `web/app/`
- `web/components/auth/`
- `web/components/workspace/`
- `web/lib/`
- control-plane docs

Disallowed files:

- backend auth API behavior
- deployment and environment files
- module product names

## Deliverables

- Code changes:
  - homepage overlay auth surface
  - protected-route redirects pointed at the overlay host
  - compatibility redirects for `/login` and `/register`
- Test changes:
  - frontend verify pass
- Docs changes:
  - update control-plane docs for the new auth entry pattern

## Acceptance Criteria

- Works correctly
- Tests pass
- Lint passes
- Type checks pass
- Build impact is addressed
- auth overlay blocks interaction with the homepage background while it is open

## Verification Commands

- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - unauthenticated user opens the overlay from the homepage, enters credentials, and lands on the requested path
- Edge case:
  - protected-path redirect lands on the homepage overlay with a preserved `next`
- Error case:
  - auth failure keeps the overlay open and shows the inline error without re-enabling background interaction

## Risks

- query-param-based overlay state can leave stale URLs if redirect cleanup is incomplete
- homepage layout changes can accidentally re-enable background interaction while the overlay is open

## Rollback Plan

- restore `/login` as the primary frontend auth surface
- revert protected-route redirects back to `/login?next=...`
