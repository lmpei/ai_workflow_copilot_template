# Task: stage-a-09-staging-delivery-path

## Goal

Turn the Stage A delivery baseline into a concrete staging path with clearer release sequencing, migration discipline,
and smoke-validation expectations.

## Project Stage

- Stage: Stage A
- Track: Delivery and Operations

## Why

The first delivery baseline documented minimum rules, but Stage A still needs a more operationally specific path that
shows how the project would move from local/dev usage into a staging-grade release routine.

## Context

Relevant documents:

- `docs/prd/STAGE_A_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `docs/development/DELIVERY_BASELINE.md`
- `docs/development/STAGING_RELEASE_PATH.md`
- `docs/development/WINDOWS_SETUP.md`
- `README.md`

Relevant operational areas:

- `.env.example`
- `docker-compose.yml`
- `scripts/`
- `server/alembic/`
- root and `docs/development/` documentation

## Flow Alignment

- Flow A / B / C / D: supports all flows operationally
- Related APIs: none directly
- Related schema or storage changes: migration and release process only if documented or minimally automated

## Dependencies

- Prior task: `tasks/archive/stage-a/stage-a-06-wave-two-planning.md`
- Blockers: none

## Scope

Allowed files:

- `README.md`
- `CONTEXT.md`
- `STATUS.md`
- `docs/development/`
- `docs/PROJECT_GUIDE.md`
- `scripts/`
- `.env.example`
- `docker-compose.yml`
- `server/alembic/`

Disallowed files:

- unrelated feature runtime code
- production-only infrastructure outside the Stage A baseline

## Deliverables

- Code changes:
  - add only the minimum script or compose adjustments needed to support a defined staging path
- Test changes:
  - none required unless a helper script or release command needs basic validation
- Docs changes:
  - define a staging-grade release sequence
  - clarify migration, smoke, and rollback expectations for staging
  - make the local/dev/staging path more concrete than the current baseline

## Acceptance Criteria

- the project documents a concrete path from local/dev usage to a staging-grade validation routine
- migration and smoke-test expectations for staging are explicit
- release helpers and docs are aligned enough that a collaborator can rehearse the staging path without hidden knowledge

## Verification Commands

- Repository:
  - manual doc consistency review
  - any affected helper scripts should run without obvious command-shape errors

## Tests

- Normal case:
  - a collaborator can follow the docs to understand the intended staging release sequence
- Edge case:
  - local shortcuts remain clearly separated from staging expectations
- Error case:
  - the staging path should not imply unsupported production guarantees

## Risks

- staging work can sprawl into full production-operations design if the scope is not kept at the Stage A level

## Rollback Plan

- revert the staging-path docs or helper changes while preserving the more general Stage A delivery baseline

## Results

- added env-file-aware Compose support for `server`, `worker`, and `web` through `APP_ENV_FILE`
- taught the migration and release preflight helpers to accept an explicit env file path
- added a minimal staging smoke helper for API health and web-root checks
- documented the concrete Stage A staging rehearsal path, including release sequencing, smoke expectations, and rollback decisions

## Execution Status

- Status: completed
- Completed At: 2026-03-18
- Notes: Stage A now has a repeatable `.env.staging`-style release rehearsal path without claiming unsupported production guarantees

## Verification Result

- manual doc consistency review
- `cmd /c scripts\migrate-windows.cmd --help`
- `cmd /c scripts\release-check-windows.cmd --help`
- `cmd /c scripts\staging-smoke-windows.cmd --help`
- `docker compose config` with `APP_ENV_FILE` override
