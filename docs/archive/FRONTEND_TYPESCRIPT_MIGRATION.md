# Frontend TypeScript Migration Assessment

## Purpose

This note records the feasibility assessment for migrating the existing Next.js frontend scaffold from JavaScript to
TypeScript before resuming `phase1-07-frontend-mvp-integration`.

## Current Frontend State

- The frontend is a small scaffold with `19` source files under `web/app/`, `web/components/`, and `web/lib/`.
- The current files were all `.js` modules when this migration was scoped.
- The current scaffold is structurally simple:
  - route shells under `web/app/`
  - small presentational components under `web/components/`
  - lightweight helpers under `web/lib/`
- The project already uses Next.js App Router and does not depend on a custom Babel or bundler setup.

## Feasibility

The migration is feasible with low architectural risk and moderate implementation effort.

Why the risk is low:

- The frontend surface is still small.
- Most pages are route shells with limited local state.
- There is no global state library to migrate.
- There is no existing complex form library or custom build tooling to untangle.
- Next.js 14 has first-class TypeScript support.

Why the effort is still non-trivial:

- The migration is not just file renaming.
- The App Router pages, components, and shared helpers all need explicit types.
- Route params, browser events, local storage helpers, fetch helpers, and API payloads all need stable interfaces.
- The migration should avoid mixing language migration with feature work from `phase1-07`.

## Recommended Scope

The TypeScript migration should include:

- add `web/tsconfig.json`
- add `web/next-env.d.ts`
- rename frontend source files from `.js` to `.ts` or `.tsx`
- type route params for App Router pages
- type shared API payloads and responses in `web/lib/`
- keep `npm run verify` green

The migration should not include:

- new product behavior
- auth UX redesign
- SSR auth guards
- state-management-library adoption
- frontend/backend API contract changes

## Recommended Sequence

1. Complete the dedicated frontend TypeScript migration task.
2. Verify `npm run verify`.
3. Resume `phase1-07-frontend-mvp-integration` on top of the TypeScript scaffold.

## Key Risks To Watch

- inconsistent typing of App Router `params`
- mixing server-only and browser-only helpers in the same module
- incomplete typing of API error shapes
- accidental feature work during the migration task

## Recommendation

Proceed with a dedicated frontend TypeScript migration before restarting the Phase 1 frontend MVP integration task.
