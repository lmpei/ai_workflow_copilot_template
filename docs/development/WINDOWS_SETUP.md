# Windows Development

This document is a Windows-specific supplement to `README.md`.
Use `README.md` as the primary project startup guide.
Use this file only for Windows shell differences, optional local dependency setup, and verification helpers.
For the Stage B release baseline, also read `docs/development/DELIVERY_BASELINE.md`.
For the concrete staging rehearsal path, read `docs/development/STAGING_RELEASE_PATH.md`.

## Recommended tools

- Python 3.11+
- Node.js 20+
- Docker Desktop

## PowerShell notes

- Use `Copy-Item` instead of `cp`
- Use `npm.cmd` in PowerShell if `npm.ps1` is blocked by execution policy
- Prefer `python -m <tool>` for Python commands inside the local virtual environment

## Project startup

From the repository root:

```powershell
Copy-Item .env.example .env
```

Then edit `.env` and replace `AUTH_SECRET_KEY=replace_me` with your own unique secret.

After that, start the stack:

```powershell
docker compose up --build
```

Before running Docker commands, make sure Docker Desktop is open and the Docker engine is running.

Useful local URLs after startup:

- Frontend: `http://localhost:3000`
- API base: `http://localhost:8000/api/v1`
- Health check: `http://localhost:8000/api/v1/health`

## Environment intent

- `local`
  - your normal Docker Compose development environment
- `dev`
  - a shared validation environment with non-placeholder secrets and environment-specific URLs
- `staging`
  - a release-like environment that must follow migration, smoke-check, evidence, and handoff discipline

## Optional local dependency setup

Use this only if you want local Python/Node development outside the Docker-only startup path.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r server\requirements.txt
cd web
npm.cmd ci
cd ..
```

## Local verification

Backend:

```powershell
cd server
..\.venv\Scripts\python -m ruff check .
..\.venv\Scripts\python -m mypy app
..\.venv\Scripts\python -m pytest
cd ..
```

Frontend:

```powershell
cd web
npm.cmd run verify
cd ..
```

## Convenience scripts

- `scripts\setup-windows.cmd`
- `scripts\verify-windows.cmd`
- `scripts\migrate-windows.cmd`
- `scripts\release-check-windows.cmd`
- `scripts\write-release-evidence-windows.cmd`
- `scripts\staging-smoke-windows.cmd`
- `scripts\staging-rehearse-windows.cmd`

These are local development and release rehearsal helpers, not project startup commands.

- `setup-windows.cmd`
  - prepares a local Windows development environment
- `verify-windows.cmd`
  - runs local backend and frontend verification
- `migrate-windows.cmd`
  - applies Alembic migrations using `DATABASE_URL` from the provided env file and runs inside the `server` container when the URL targets the local Compose `db` hostname
- `release-check-windows.cmd`
  - validates env-file alignment, rejects placeholder secrets, and then runs the verification baseline
- `write-release-evidence-windows.cmd`
  - writes a reusable Stage B release evidence record with the env file, change ref, rollback target, checked URLs, and companion handoff path
- `staging-smoke-windows.cmd`
  - checks the health endpoint and web root derived from the provided env file
- `staging-rehearse-windows.cmd`
  - runs the Stage B staging preflight, compose validation, startup, migration, force-recreate, smoke checks, and writes both release evidence and a handoff note

Run them from PowerShell with:

```powershell
cmd /c scripts\setup-windows.cmd
cmd /c scripts\verify-windows.cmd
cmd /c scripts\migrate-windows.cmd .env
cmd /c scripts\release-check-windows.cmd .env
cmd /c scripts\write-release-evidence-windows.cmd .env.staging <rollback-target>
cmd /c scripts\staging-smoke-windows.cmd .env
cmd /c scripts\staging-rehearse-windows.cmd .env.staging <rollback-target> app-tier C:\staging\handoff.md C:\staging\evidence.md
```

## Stage B staging rehearsal

Recommended Windows rehearsal flow:

1. copy `.env.example` to `.env.staging`
2. set `APP_ENV_FILE=.env.staging` inside `.env.staging`
3. replace all placeholder secrets and update the environment URLs
4. pick a rollback target before you start the rehearsal
5. run `cmd /c scripts\staging-rehearse-windows.cmd .env.staging <rollback-target> app-tier <handoff-file> <evidence-file>`
6. keep the generated evidence and handoff files, or fill `docs/development/STAGING_RELEASE_EVIDENCE_TEMPLATE.md` and `docs/development/STAGING_HANDOFF_TEMPLATE.md` outside git if you used the manual path

If you need the manual step-by-step version instead of the helper, use `docs/development/STAGING_RELEASE_PATH.md`.