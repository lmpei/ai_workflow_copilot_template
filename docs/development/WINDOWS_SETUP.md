# Windows Development

This document is a Windows-specific supplement to `README.md`.
Use `README.md` as the primary project startup guide.
Use this file only for Windows shell differences, optional local dependency setup, and verification helpers.
For the Stage A release baseline, also read `docs/development/DELIVERY_BASELINE.md`.
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
  - a release-like environment that must follow migration and smoke-check discipline

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
- `scripts\staging-smoke-windows.cmd`

These are local development helpers, not project startup commands.

- `setup-windows.cmd`
  - prepares a local Windows development environment
- `verify-windows.cmd`
  - runs local backend and frontend verification
- `migrate-windows.cmd`
  - applies Alembic migrations using `DATABASE_URL` from the provided env file and runs inside the `server` container when the URL targets the local Compose `db` hostname
- `release-check-windows.cmd`
  - fails if the provided env file still contains `replace_me` and then runs the verification baseline
- `staging-smoke-windows.cmd`
  - checks the health endpoint and web root derived from the provided env file

Run them from PowerShell with:

```powershell
cmd /c scripts\setup-windows.cmd
cmd /c scripts\verify-windows.cmd
cmd /c scripts\migrate-windows.cmd .env
cmd /c scripts\release-check-windows.cmd .env
cmd /c scripts\staging-smoke-windows.cmd .env
```

## Stage A staging rehearsal

Recommended Windows rehearsal flow:

1. copy `.env.example` to `.env.staging`
2. set `APP_ENV_FILE=.env.staging` inside `.env.staging`
3. replace all placeholder secrets and update the environment URLs
4. run `cmd /c scripts\release-check-windows.cmd .env.staging`
5. run `docker compose --env-file .env.staging up -d --build server worker web`
6. run `cmd /c scripts\migrate-windows.cmd .env.staging`
7. run `cmd /c scripts\staging-smoke-windows.cmd .env.staging`

Use `docs/development/STAGING_RELEASE_PATH.md` for the full checklist, restart guidance, and rollback expectations.
