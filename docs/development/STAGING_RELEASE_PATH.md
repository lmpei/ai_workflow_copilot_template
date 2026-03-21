# Stage B Staging Release Path

This document turns the Stage B delivery baseline into a concrete staging rehearsal path.

It does not define a production deployment system. It defines the smallest repeatable path that a collaborator can use
to rehearse a release-like validation routine with explicit environment selection, migration sequencing, smoke checks,
rollback decisions, and companion evidence plus handoff artifacts.

## Supported Stage B Shape

Stage B supports a lightweight staging path built from four inputs:

- an environment-specific env file such as `.env.staging`
- Docker Compose startup for the application services
- Windows helper scripts for preflight, migration, smoke, release evidence, and full rehearsal
- a release evidence record plus a handoff note that record what changed, what was checked, and what rollback target applies

This path is intentionally limited:

- it does not promise zero-downtime release behavior
- it does not include production-grade secret rotation
- it does not include automated rollback orchestration
- it does not replace the broader baseline in `docs/development/DELIVERY_BASELINE.md`

## Environment File Convention

For a staging rehearsal, keep a dedicated env file outside version control.

Recommended pattern:

- `.env`
  - normal local development
- `.env.dev`
  - shared internal validation
- `.env.staging`
  - release-like staging validation

The Compose file honors `APP_ENV_FILE`, so the selected env file can also be passed into the `server`, `worker`, and
`web` containers. Stage B now expects the selected env file and `APP_ENV_FILE` value to match.

A staging env file should include:

- `APP_ENV_FILE=.env.staging`
- non-placeholder values for all live secrets
- staging-specific `DATABASE_URL`, `REDIS_URL`, and `CHROMA_URL`
- staging-specific `NEXT_PUBLIC_API_BASE_URL` and `INTERNAL_API_BASE_URL`
- optional `STAGING_WEB_URL` if the web root should differ from the API-host-derived default

## Release Owner Checklist

Before a staging rehearsal starts, confirm:

1. the target env file exists and is not committed to git
2. the target env file contains no `replace_me` placeholders
3. `APP_ENV_FILE` matches the env file being rehearsed
4. the target environment URLs and secrets are current
5. the release owner knows which prior image or code revision is the rollback target
6. a database backup or a known-safe recovery path exists for incompatible schema failures

## Stage B Staging Release Sequence

### 1. Preflight

Run the repository verification baseline against the staging env file:

```powershell
cmd /c scripts\release-check-windows.cmd .env.staging
```

This confirms:

- the env file exists
- `APP_ENV_FILE` is aligned
- no placeholder secrets remain
- backend and frontend verification still pass locally before the release rehearsal continues

### 2. Start or Refresh the Staging Candidate

For a local rehearsal that still uses bundled Compose backing services:

```powershell
docker compose --env-file .env.staging up -d --build
```

For a shared staging rehearsal that points at external backing services and only needs the application tier:

```powershell
docker compose --env-file .env.staging up -d --build server worker web
```

Use the second form only when the env file already points at environment-specific `DATABASE_URL`, `REDIS_URL`, and
`CHROMA_URL` values.

### 3. Apply Migrations

Run migrations against the same env file:

```powershell
cmd /c scripts\migrate-windows.cmd .env.staging
```

The helper reads `DATABASE_URL` from the provided env file and applies `alembic upgrade head`. If the URL uses the
local Compose hostname `db`, it runs inside the `server` container so the database is reachable on the Compose network.

### 4. Recreate the Application Tier

After migration, force-recreate the application tier so code and env changes are definitely applied:

```powershell
docker compose --env-file .env.staging up -d --build --force-recreate server worker web
```

### 5. Automated Smoke

Run the minimum staging smoke helper:

```powershell
cmd /c scripts\staging-smoke-windows.cmd .env.staging
```

The helper checks:

- `NEXT_PUBLIC_API_BASE_URL + /health`
- the web root derived from `STAGING_WEB_URL` or from the API base URL

### 6. Manual Smoke

The release is not considered rehearsed until a human completes these checks:

- login succeeds
- a workspace loads
- the documents view loads without server errors
- a Research task can run to completion
- the formal Research report path can complete
- traces and task history remain visible after the run

### 7. Evidence and Handoff Records

Record the rehearsal outcome before handing off the release candidate.

Preferred helper:

```powershell
cmd /c scripts\staging-rehearse-windows.cmd .env.staging <rollback-target> app-tier C:\staging\handoff.md C:\staging\evidence.md
```

This helper runs the Stage B routine end to end and writes:

- a release evidence record to `%TEMP%\ai_workflow_copilot_staging_evidence.md` by default, or to a custom path when one is provided
- a handoff note to `%TEMP%\ai_workflow_copilot_staging_handoff.md` by default, or to a custom path when one is provided

Fallback path:

- copy `docs/development/STAGING_RELEASE_EVIDENCE_TEMPLATE.md` outside git
- copy `docs/development/STAGING_HANDOFF_TEMPLATE.md` outside git
- fill in the env file, change ref, rollback target, automated steps completed, checked URLs, and any operator notes

## Failure Handling

### Preflight Failure

- do not continue the release
- fix secrets, verification failures, or repository drift first

### Migration Failure

- do not restart into the new release candidate
- correct the migration issue before retrying
- if schema state is uncertain, recover the database before another attempt

### Smoke Failure After Restart

- revert to the previous code or image version
- reconcile schema state before retrying
- log which smoke step failed so the next rehearsal starts from a known state

## Minimum Rollback Decision Path

The Stage B rollback decision path is:

1. identify whether failure happened before migration, during migration, or after app restart
2. stop the release if migration did not complete cleanly
3. restore the prior code or image target if the restarted release is unhealthy
4. restore the database from backup or use a known-safe downgrade only when the schema state requires it
5. rerun preflight before attempting another staging rehearsal

## Related Docs

- `docs/development/DELIVERY_BASELINE.md`
- `docs/development/STAGING_RELEASE_EVIDENCE_TEMPLATE.md`
- `docs/development/STAGING_HANDOFF_TEMPLATE.md`
- `docs/development/WINDOWS_SETUP.md`
- `README.md`
- `tasks/archive/stage-a/stage-a-09-staging-delivery-path.md`