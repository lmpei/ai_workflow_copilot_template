# Task: frontend_typescript_migration

## Goal

Migrate the existing Next.js frontend scaffold from JavaScript to TypeScript before resuming `phase1-07-frontend-mvp-integration`.

## Project Phase

- Phase: `Phase 1 support work`
- Scenario module: `shared platform core`

## Why

The project direction is to use TypeScript as the default frontend language. Doing the migration now is cheaper and
cleaner than first completing `phase1-07` in JavaScript and migrating later.

## Context

Relevant specs:

- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/archive/FRONTEND_TYPESCRIPT_MIGRATION.md`
- `docs/PROJECT_GUIDE.md`

Current state:

- the frontend scaffold was still JavaScript-based when this task was scoped
- `phase1-07-frontend-mvp-integration` has been intentionally rolled back
- future frontend work should default to TypeScript

## Scope

Allowed files:

- `web/app/`
- `web/components/`
- `web/lib/`
- `web/tsconfig.json`
- `web/next-env.d.ts`
- `web/package.json`
- `web/next.config.js`

Disallowed files:

- `server/`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `tasks/phase1-07-frontend-mvp-integration.md`

## Deliverables

- Code changes:
  - add Next.js TypeScript project config
  - convert existing frontend source files from `.js` to `.ts` / `.tsx`
  - add explicit types for route params, props, auth helpers, and shared API helpers
  - keep behavior equivalent to the current scaffold
- Test changes:
  - none required beyond existing frontend verification
- Docs changes:
  - none required in this task

## Acceptance Criteria

- frontend source files under `web/app/`, `web/components/`, and `web/lib/` are TypeScript-based
- `npm run lint` passes
- `npm run build` passes
- no Phase 1 integration behavior is added in this task
- `phase1-07-frontend-mvp-integration` can restart on top of the migrated scaffold

## Verification Commands

- Frontend:
  - `cd web`
  - `npm.cmd run verify`

## Tests

- Normal case: the existing scaffold pages still build and render
- Edge case: dynamic App Router pages compile with typed `params`
- Error case: TypeScript configuration does not introduce build errors

## Risks

- mixing language migration with feature work will make review harder and increase rollback cost

## Rollback Plan

- revert the TypeScript migration changes and restore the JavaScript scaffold
