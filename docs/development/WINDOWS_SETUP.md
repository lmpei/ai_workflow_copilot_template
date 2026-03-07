# Windows Development

This repository supports local development on Windows with PowerShell or Command Prompt.

## Recommended tools

- Python 3.11+
- Node.js 20+
- Docker Desktop

## PowerShell notes

- Use `Copy-Item` instead of `cp`
- Use `npm.cmd` in PowerShell if `npm.ps1` is blocked by execution policy
- Prefer `python -m <tool>` for Python commands inside the local virtual environment

## Quick start

From the repository root:

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\python -m pip install -r server\requirements.txt
cd web
npm.cmd ci
cd ..
docker compose up --build
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

Run them from PowerShell with:

```powershell
cmd /c scripts\setup-windows.cmd
cmd /c scripts\verify-windows.cmd
```
