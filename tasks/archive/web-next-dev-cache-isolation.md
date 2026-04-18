# Task

- ID: TEMP-2026-04-17-WEB-NEXT-DEV-CACHE
- Title: isolate Next dev build artifacts so refresh no longer requires rebuilds
- Status: completed

## Goal

Fix the unstable frontend dev loop where refreshing the browser can trigger runtime chunk errors and force a manual
rebuild.

## Scope

- isolate `web` service dev-time `.next` artifacts from the bind-mounted workspace
- reset stale dev artifacts when the `web` container starts
- document the one-time recreate step for the updated local dev flow

## Verification

- `docker compose config`
- `npm --prefix web run verify`
- `git diff --check`
