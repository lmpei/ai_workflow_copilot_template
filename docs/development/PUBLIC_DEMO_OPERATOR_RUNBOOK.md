# Public Demo Operator Runbook

## Purpose

This document defines the bounded operator routine added in `stage-d-04`.

It is not a production operations manual. It is the smallest honest routine for keeping the public demo reachable,
refreshable, and recoverable without relying on hidden tribal knowledge.

## Current Operator Contract

The public demo baseline now has three layers:

1. `stage-d-02`
   - public-demo guardrails and a backend-owned settings contract
2. `stage-d-03`
   - backend-owned guided demo templates plus seeded workspace creation
3. `stage-d-04`
   - a repeatable operator path for restart, refresh, smoke, and rollback decisions

## Scripts

Use these scripts for public-demo operations on Windows:

- `scripts\release-check-windows.cmd <env-file>`
  - validates env-file alignment and rejects placeholder secrets
- `scripts\public-demo-smoke-windows.cmd <env-file>`
  - checks API health, the public-demo settings endpoint, the template catalog, and the web root
- `scripts\public-demo-refresh-windows.cmd <env-file> [service-mode]`
  - runs preflight, compose config validation, startup, migration, force-recreate, and public-demo smoke

`service-mode` can be:

- `app-tier`
- `full-stack`

## Restart Path

Use this when the public demo is unhealthy but the data does not need a clean refresh:

```powershell
cmd /c scripts\release-check-windows.cmd .env
cmd /c scripts\migrate-windows.cmd .env
cmd /c scripts\public-demo-refresh-windows.cmd .env app-tier
```

Use `full-stack` only when the environment still depends on bundled Compose backing services and those services also
need to be recreated.

## Refresh Path

Use this when the public demo is reachable but you want a clean showcase path for new viewers.

1. run the bounded refresh routine:

```powershell
cmd /c scripts\public-demo-refresh-windows.cmd .env app-tier
```

2. sign in with:
   - a reserved operator demo account with free workspace slots, or
   - a fresh demo account if self-serve registration is enabled
3. create a new guided demo workspace from `Workspace Hub`
4. confirm the seeded walkthrough still works in this order:
   - `Documents`
   - `Chat`
   - `Tasks`

## Smoke Checklist

The automated public-demo smoke only proves that the public surfaces are reachable.
A human still needs to confirm:

- login works
- `Workspace Hub` loads
- guided demo cards appear on the home page or workspace entry path
- a guided demo workspace can be created
- the seeded workspace overview shows the guided showcase panel
- one module workflow can be exercised end to end without hidden operator setup

## Registration and Abuse Response

Disable self-serve registration when:

- the environment becomes unstable
- you need to preserve limited demo capacity for a scheduled walkthrough
- you suspect abusive use or spam signups

The operator-facing switch remains:

- `PUBLIC_DEMO_REGISTRATION_ENABLED=false`

This is a bounded demo control, not a full abuse-prevention system.

## Rollback Expectations

The public demo rollback decision path is still manual and intentionally lightweight.

If preflight fails:

- do not refresh the demo
- fix the env file, secrets, or repository drift first

If migration fails:

- stop the rollout
- keep or restore the prior healthy application state before retrying

If the refreshed application starts but the public-demo smoke fails:

- revert to the prior code or image version
- reconcile schema state if the migration changed it incompatibly
- rerun preflight before the next attempt

## Honest Boundaries

This runbook does not promise:

- zero-downtime deployment
- production-grade rollback orchestration
- automatic cleanup of user-created demo workspaces
- permanent refresh of showcase data without operator judgment

Today, the honest refresh path is to create a fresh guided demo workspace with a reserved or fresh account, or to reset
the environment outside this repo's bounded automation when a clean slate is required.

## Related Docs

- `docs/development/PUBLIC_DEMO_BASELINE.md`
- `docs/development/PUBLIC_DEMO_SHOWCASE_PATH.md`
- `docs/development/PUBLIC_DEPLOYMENT_CONTRACT.md`
- `docs/development/DELIVERY_BASELINE.md`
- `docs/development/STAGING_RELEASE_PATH.md`
- `docs/prd/STAGE_D_PLAN.md`