# Public Deployment Path

## Purpose

This document turns the public hosting contract from `docs/development/PUBLIC_DEPLOYMENT_CONTRACT.md` into one bounded
repository-side deployment path.

It does not claim that the public demo is already rolled out. It only defines the concrete repo artifacts, env shape,
and operator commands that make the rollout rehearsal in `stage-d-08` possible.

## Repo Artifacts

Stage D-07 adds one bounded deployment path made of these files:

- `docker-compose.public-demo.yml`
  - standalone Compose file for the first public-demo VM target
- `server/Dockerfile.deploy`
  - non-reload FastAPI container for the public demo
- `web/Dockerfile.deploy`
  - built Next.js container for the public demo
- `deploy/public-demo/Caddyfile`
  - reverse-proxy routing for `app.<domain>` and `api.<domain>`
- `.env.public-demo.example`
  - tracked scaffold showing the expected env shape for the public rollout
- `scripts/public-demo-deploy-windows.cmd`
  - bounded Windows helper for preflight, Compose validation, startup, migration, recreate, and public-demo smoke

These files exist to support the first rollout target only:

- one public Linux VM
- Docker Engine + Docker Compose
- one reverse proxy with automatic TLS where possible

## External Prerequisites

The repo-side deployment path still assumes a human has already prepared:

1. one public Linux VM
2. Docker Engine and Docker Compose on that VM
3. DNS for:
   - `app.<domain>`
   - `api.<domain>`
4. public ports for the reverse proxy entrypoint
5. an environment-specific env file outside git with real secrets

Those steps remain manual and are intentionally outside the repo.

## Environment File Shape

Use `.env.public-demo.example` only as a template.

Before a real rollout:

1. copy it outside git to a file such as `.env.public-demo`
2. replace every `replace_me`
3. change `APP_ENV_FILE` so it matches the selected env file path or basename
4. set:
   - `NEXT_PUBLIC_API_BASE_URL=https://api.<domain>/api/v1`
   - `INTERNAL_API_BASE_URL=http://server:8000/api/v1`
   - `PUBLIC_WEB_URL=https://app.<domain>`
   - `PUBLIC_WEB_HOST=app.<domain>`
   - `PUBLIC_API_HOST=api.<domain>`
   - `CORS_ORIGINS=https://app.<domain>`
   - `PUBLIC_DEMO_MODE=true`
   - `PUBLIC_DEMO_REGISTRATION_ENABLED` intentionally

## Bounded Deployment Sequence

### 1. Preflight

```powershell
cmd /c scripts\release-check-windows.cmd .env.public-demo
```

### 2. Compose Validation Plus Startup

```powershell
cmd /c scripts\public-demo-deploy-windows.cmd .env.public-demo full-stack
```

This helper now performs:

- release preflight
- `docker compose --env-file <env-file> config` using `docker-compose.public-demo.yml`
- startup of the chosen service mode
- migration through `scripts\migrate-windows.cmd`
- force-recreate of `server`, `worker`, `web`, and `reverse-proxy`
- `scripts\public-demo-smoke-windows.cmd`

### 3. Human Smoke Still Required

The deployment path is not complete until a human confirms:

- login works
- `Workspace Hub` loads
- a guided demo workspace can be created
- one seeded path still reaches `Documents -> Chat -> Tasks`

That manual check remains part of `stage-d-08`.

## Service Modes

`scripts\public-demo-deploy-windows.cmd` supports:

- `full-stack`
  - use this for the chosen first rollout target on one VM
- `app-tier`
  - use this only if the environment already supplies compatible backing services elsewhere

The default remains `full-stack` because the chosen first public target keeps the bundled Compose backing services.

## Honest Boundaries

This path still does not promise:

- zero-downtime deployment
- automated rollback orchestration
- production-grade secret rotation
- managed-database hosting
- platform-specific hardening beyond the first bounded VM rollout

## Related Docs

- `docs/development/PUBLIC_DEMO_BASELINE.md`
- `docs/development/PUBLIC_DEMO_OPERATOR_RUNBOOK.md`
- `docs/development/PUBLIC_DEPLOYMENT_CONTRACT.md`
- `docs/development/DELIVERY_BASELINE.md`
- `docs/prd/STAGE_D_PLAN.md`
