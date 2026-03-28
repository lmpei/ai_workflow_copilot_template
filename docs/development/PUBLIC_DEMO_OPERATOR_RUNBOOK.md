# Public Demo Operator Runbook

## Purpose

This document defines the bounded operator routine added in `stage-d-04`, extended in `stage-d-07`, prepared for the
rollout-evidence path in `stage-d-08`, and clarified for persistent Stage E workbench continuity.

It is not a production operations manual. It is the smallest honest routine for keeping the public demo reachable,
refreshable, and recoverable without relying on hidden tribal knowledge.

## Current Operator Contract

The public demo baseline now has six layers:

1. `stage-d-02`
   - public-demo guardrails and a backend-owned settings contract
2. `stage-d-03`
   - backend-owned guided demo templates plus seeded workspace creation
3. `stage-d-04`
   - a repeatable operator path for restart, refresh, smoke, and rollback decisions
4. `stage-d-07`
   - one bounded deployment path for the chosen public VM target
5. `stage-d-08`
   - one bounded rollout-evidence and handoff path for the first public rehearsal
6. `stage-e-04`
   - one bounded continuity contract for Support cases and Job hiring packets in the live public demo

## Scripts

Use these scripts for public-demo operations on Windows:

- `scripts\release-check-windows.cmd <env-file>`
  - validates env-file alignment and rejects placeholder secrets
- `scripts\public-demo-smoke-windows.cmd <env-file>`
  - checks API health, the public-demo settings endpoint, the template catalog, the web root, the login page, and the workspace page
- `scripts\public-demo-refresh-windows.cmd <env-file> [service-mode]`
  - runs preflight, compose config validation, startup, migration, force-recreate, and public-demo smoke for the existing local-style Compose stack
- `scripts\public-demo-deploy-windows.cmd <env-file> [service-mode]`
  - runs the bounded public rollout path through `docker-compose.public-demo.yml`
- `scripts\write-public-demo-rollout-evidence-windows.cmd <env-file> <rollback-target> [service-mode] [evidence-file] [handoff-file]`
  - writes the rollout evidence artifact for the public-demo rehearsal
- `scripts\public-demo-rehearse-windows.cmd <env-file> <rollback-target> [service-mode] [handoff-file] [evidence-file]`
  - runs the bounded public-demo deploy path and writes rollout evidence plus a handoff note

`service-mode` can be:

- `app-tier`
- `full-stack`

For the chosen first public rollout target, prefer `full-stack` unless the backing services have already been moved out
of the VM-hosted Compose stack.

## Deploy Path

Use this when you want the repository-side public rollout path rather than a local refresh routine:

```powershell
cmd /c scripts\release-check-windows.cmd .env.public-demo
cmd /c scripts\public-demo-deploy-windows.cmd .env.public-demo full-stack
```

This path assumes the VM, DNS, TLS reachability, and the real env file already exist.
Those prerequisites remain manual.

When you want to capture the rollout rehearsal and its artifacts in one pass:

```powershell
cmd /c scripts\public-demo-rehearse-windows.cmd .env.public-demo <rollback-target> full-stack
```

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
4. treat old workspaces as allowed to keep accumulated Support case and Job hiring-packet state; do not rely on hidden
   in-place cleanup before a walkthrough
5. confirm the seeded walkthrough still works in this order:
   - `Documents`
   - `Chat`
   - `Tasks`
6. if you intentionally reopen an older Support or Job workspace, explain the honest entry rule up front:
   - Support continues from the visible Support case workbench
   - Job continues from the visible Job hiring-packet workbench
   - a clean story still comes from a new guided demo workspace, not from quiet page-level reset

If a new viewer needs a clean story, the honest Stage E path is to use a fresh guided demo workspace rather than to
quietly scrub existing workbench objects.

## Smoke Checklist

The automated public-demo smoke only proves that the public surfaces are reachable.
A human still needs to confirm:

- login works
- `Workspace Hub` loads
- guided demo cards appear on the home page or workspace entry path
- a guided demo workspace can be created
- the seeded workspace overview shows the guided showcase panel
- one module workflow can be exercised end to end without hidden operator setup

When Stage E workbench continuity matters for the walkthrough, also confirm:

- a Support demo path can generate or reopen at least one visible Support case
- the latest Support case event can still link back to the task that produced it
- the next Support follow-up can be started directly from the visible case
- a Job demo path can generate or reopen at least one visible Job hiring packet
- the latest Job hiring-packet event can still link back to the task that produced it
- the next Job shortlist refresh or review can be started directly from the visible packet
- the viewer-facing entry rule is still understandable without operator narration:
  - fresh story -> new guided demo workspace
  - existing Support work -> visible case workbench
  - existing Job work -> visible hiring-packet workbench

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
- automatic cleanup of Support case or Job hiring-packet state inside an existing workspace
- permanent refresh of showcase data without operator judgment

Today, the honest refresh path is to create a fresh guided demo workspace with a reserved or fresh account. If a true
clean slate is required, reset the environment outside this repo's bounded automation.

## Related Docs

- `docs/development/PUBLIC_DEMO_BASELINE.md`
- `docs/development/PUBLIC_DEMO_WORKBENCH_CONTINUITY.md`
- `docs/development/PUBLIC_DEMO_SHOWCASE_PATH.md`
- `docs/development/PUBLIC_DEPLOYMENT_CONTRACT.md`
- `docs/development/PUBLIC_DEPLOYMENT_PATH.md`
- `docs/development/PUBLIC_DEMO_ROLLOUT_EVIDENCE_TEMPLATE.md`
- `docs/development/PUBLIC_DEMO_ROLLOUT_HANDOFF_TEMPLATE.md`
- `docs/development/DELIVERY_BASELINE.md`
- `docs/development/STAGING_RELEASE_PATH.md`
- `docs/prd/STAGE_D_PLAN.md`
