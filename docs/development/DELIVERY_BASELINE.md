# Stage A Delivery Baseline

This document defines the minimum delivery and operations baseline for Stage A.

It does not describe a full production platform. It defines the smallest repeatable path from local development toward
shared `dev` or `staging` delivery.

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

## Configuration and Secret Rules

`.env.example` is a local scaffold, not a deployable environment file.

Rules:

- `AUTH_SECRET_KEY` must never remain `replace_me`
- any provider key that remains in use must not remain `replace_me`
- local Compose database defaults are for `local` only
- `dev` and `staging` should override `DATABASE_URL`, `REDIS_URL`, and `CHROMA_URL` for the target environment
- `NEXT_PUBLIC_API_BASE_URL` and `INTERNAL_API_BASE_URL` should match the environment being released

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
cmd /c scripts\migrate-windows.cmd
```

Direct command:

```powershell
cd server
..\.venv\Scripts\python.exe -m alembic upgrade head
cd ..
```

## Release Preflight

Use the Windows helper for the minimum Stage A release preflight:

```powershell
cmd /c scripts\release-check-windows.cmd
```

This helper:

- verifies `.env` exists
- fails if `.env` still contains `replace_me`
- runs the repository verification baseline

It does not run migrations automatically.

## Minimum Release Flow

For a Stage A `local`, `dev`, or `staging` release candidate:

1. ensure `.env` is present and all live secrets are set
2. run `cmd /c scripts\release-check-windows.cmd`
3. run `cmd /c scripts\migrate-windows.cmd`
4. restart or recreate the application services
5. run a smoke check

Minimum smoke check:

- `/api/v1/health` responds successfully
- login works
- a workspace can load
- documents view loads
- Research tasks can run
- the Research report path can complete

## Rollback and Recovery

Stage A rollback is intentionally lightweight.

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

Stage A does not assume automated rollback orchestration. The minimum requirement is that the release owner has a
documented manual decision path.

## Minimum Runbook

The minimum operational runbook for Stage A is:

- startup:
  - `docker compose up --build` for local
  - environment-specific startup command for `dev` or `staging`
- verify:
  - `cmd /c scripts\release-check-windows.cmd`
- migrate:
  - `cmd /c scripts\migrate-windows.cmd`
- smoke:
  - health, login, workspace load, Research task, Research report
- rollback:
  - restore the previous code/image version and reconcile schema state before retrying
