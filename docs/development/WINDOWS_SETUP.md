# Windows Development

This document is a Windows-specific supplement to `README.md`.
Use `README.md` as the primary project startup guide.
Use this file only for Windows shell differences, optional local dependency setup, and verification helpers.

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
docker compose up --build
```

Before running Docker commands, make sure Docker Desktop is open and the Docker engine is running.

Useful local URLs after startup:

- Frontend: `http://localhost:3000`
- API base: `http://localhost:8000/api/v1`
- Health check: `http://localhost:8000/api/v1/health`

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

These are local development helpers, not project startup commands.

- `setup-windows.cmd`
  - prepares a local Windows development environment
- `verify-windows.cmd`
  - runs local backend and frontend verification

Run them from PowerShell with:

```powershell
cmd /c scripts\setup-windows.cmd
cmd /c scripts\verify-windows.cmd
```
