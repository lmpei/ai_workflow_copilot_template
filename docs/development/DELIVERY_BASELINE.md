# Stage B Delivery Baseline

This document defines the minimum delivery and operations baseline for Stage B.

It does not describe a full production platform. It defines the smallest repeatable path from local development toward
shared `dev` or `staging` delivery, plus the first operator-friendly rehearsal routine, release evidence, and handoff
expectations.

For the concrete Stage B staging rehearsal sequence, also read `docs/development/STAGING_RELEASE_PATH.md`.
For the Stage C cross-module demo baseline, also read `docs/development/STAGE_C_CROSS_MODULE_READINESS.md`.

## Environment Intent

### `local`

Use `local` for day-to-day development on one machine.

- startup path: `docker compose up --build`
- default backing services: local Compose `db`, `redis`, and `chroma`
- configuration source: local `.env`
- data durability expectation: disposable unless you intentionally preserve volumes

### `dev`

Use `dev` for shared internal validation when you want a stable URL or shared integration surface.

- should not rely on placeholder secrets
- should use environment-specific backing services and URLs
- should run migrations before application restart
- should be safe for repeated smoke tests and demo verification

### `staging`

Use `staging` for release-like validation before any stronger deployment target.

- must use environment-specific secrets and service URLs
- must follow the release checklist
- must have an explicit migration step
- must support a documented rollback decision, even if rollback is manual
- must leave both a rehearsal evidence record and a handoff record describing what changed and what rollback target is expected

## Configuration and Secret Rules

`.env.example` is a local scaffold, not a deployable environment file.

Rules:

- `AUTH_SECRET_KEY` must never remain `replace_me`
- any provider key that remains in use must not remain `replace_me`
- local Compose database defaults are for `local` only
- `dev` and `staging` should override `DATABASE_URL`, `REDIS_URL`, and `CHROMA_URL` for the target environment
- `NEXT_PUBLIC_API_BASE_URL` and `INTERNAL_API_BASE_URL` should match the environment being released
- environment-specific env files should set `APP_ENV_FILE` to their own path so Compose can pass the same file into the
  application containers

Recommended practice:

- keep `.env.example` only as a template
- maintain environment-specific values outside git
- treat provider keys and auth secrets as required release inputs, not optional follow-up steps

## Migration Baseline

Alembic reads `DATABASE_URL` directly from the environment through `server/alembic/env.py`.

Minimum migration rule:

1. point `DATABASE_URL` at the target environment
2. run migrations before or during the release window
3. verify the migration step succeeds before relying on new application code

Windows helper:

```powershell
cmd /c scripts\migrate-windows.cmd .env.staging
```

When `DATABASE_URL` uses the local Compose hostname `db`, the helper runs Alembic inside the `server` container so the
database is reachable from the same network. When `DATABASE_URL` points at a host-accessible database, it falls back
to the local Python environment.

## Release Preflight

Use the Windows helper for the minimum Stage B release preflight:

```powershell
cmd /c scripts\release-check-windows.cmd .env.staging
```

This helper now confirms:

- the env file exists
- `APP_ENV_FILE` matches the selected env file
- no placeholder secrets remain
- backend and frontend verification still pass locally

## Minimum Release Flow

For a Stage B `local`, `dev`, or `staging` release candidate:

1. ensure the chosen env file is present, current, and aligned with `APP_ENV_FILE`
2. run `cmd /c scripts\release-check-windows.cmd <env-file>`
3. run `cmd /c scripts\migrate-windows.cmd <env-file>`
4. restart or recreate the application services
5. run a smoke check
6. record the rollback target, release evidence, and release handoff note

Minimum smoke check:

- `cmd /c scripts\staging-smoke-windows.cmd <env-file>` passes
- login works
- a workspace can load
- documents view loads
- Research, Support, and Job module surfaces are visible from the workspace hub or otherwise explicitly documented as unavailable
- each module can run its default workflow task or return an honest degraded result when context is thin
- the eval surface shows the module quality baseline and pass threshold for the candidate under review

## Stage B Rehearsal Helper

Use the Stage B helper when you want a single repeatable Windows rehearsal routine:

```powershell
cmd /c scripts\staging-rehearse-windows.cmd .env.staging <rollback-target> app-tier C:\staging\handoff.md C:\staging\evidence.md
```

This helper:

- runs release preflight
- validates `docker compose --env-file <env-file> config`
- starts or refreshes the chosen service shape
- applies migrations
- force-recreates the application tier
- runs the minimum smoke helper
- writes a release evidence record plus a handoff note with the env file, change ref, rollback target, and completed automated steps

It is intentionally lightweight. It does not replace manual smoke, production orchestration, or full incident handling.

## Release Evidence Baseline

Each Stage B staging rehearsal should capture:

- which env file was used
- which change ref was rehearsed
- which rollback target should be used if the release is unhealthy
- which automated checks completed
- which automated targets were actually checked
- which manual smoke checks are still required or already performed
- anything unusual that the next operator should know

Use `docs/development/STAGING_RELEASE_EVIDENCE_TEMPLATE.md` and `docs/development/STAGING_HANDOFF_TEMPLATE.md` as the
fallback shapes when the helper is not used.

## Rollback and Recovery

Stage B rollback is still intentionally lightweight.

If preflight fails:

- do not release
- fix configuration, code, or migration issues first

If migration fails before the app restart:

- keep the previous app version in place
- correct the migration problem before retrying

If the app restarts but the release is unhealthy:

- revert to the previous code or image version
- if the schema change is incompatible, restore the database from backup or use a known safe downgrade path before
  retrying

Stage B still does not assume automated rollback orchestration. The minimum requirement is that the release owner has a
documented manual decision path and an explicit rollback target.

## Minimum Runbook

The minimum operational runbook for Stage B is:

- startup:
  - `docker compose up --build` for local
  - environment-specific startup command for `dev` or `staging`
- verify:
  - `cmd /c scripts\release-check-windows.cmd <env-file>`
- migrate:
  - `cmd /c scripts\migrate-windows.cmd <env-file>`
- smoke:
  - `cmd /c scripts\staging-smoke-windows.cmd <env-file>` plus manual validation
- rehearse:
  - `cmd /c scripts\staging-rehearse-windows.cmd <env-file> <rollback-target> app-tier <handoff-file> <evidence-file>` when you want the full Stage B routine
- handoff:
  - keep the generated evidence and handoff files or copy `docs/development/STAGING_RELEASE_EVIDENCE_TEMPLATE.md` and
    `docs/development/STAGING_HANDOFF_TEMPLATE.md` outside git
- rollback:
  - restore the previous code/image version and reconcile schema state before retrying

## Stage C Cross-Module Extension

When the candidate is intended to represent Stage C readiness rather than only Stage B release hygiene:

- use `docs/development/STAGE_C_CROSS_MODULE_READINESS.md` as the shared demo checklist
- record which Research, Support, and Job surfaces were actually checked
- confirm module outputs stay honest when context is thin instead of pretending grounding exists
- confirm the eval surface exposes the registry-backed quality baseline and pass threshold for the reviewed module
