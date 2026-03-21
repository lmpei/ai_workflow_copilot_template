@echo off
setlocal EnableExtensions EnableDelayedExpansion

if /I "%~1"=="--help" goto usage

set "ENV_FILE=%~1"
if "%ENV_FILE%"=="" set "ENV_FILE=.env.staging"

set "ROLLBACK_TARGET=%~2"
if "%ROLLBACK_TARGET%"=="" (
  echo Missing rollback target. Provide a prior image tag, commit, or release label.
  exit /b 1
)

set "SERVICE_MODE=%~3"
if "%SERVICE_MODE%"=="" set "SERVICE_MODE=app-tier"

if /I not "%SERVICE_MODE%"=="app-tier" if /I not "%SERVICE_MODE%"=="full-stack" (
  echo Unsupported service mode %SERVICE_MODE%. Use app-tier or full-stack.
  exit /b 1
)

set "EVIDENCE_FILE=%~4"
if "%EVIDENCE_FILE%"=="" set "EVIDENCE_FILE=%TEMP%\ai_workflow_copilot_staging_evidence.md"

set "HANDOFF_FILE=%~5"
if "%HANDOFF_FILE%"=="" set "HANDOFF_FILE=%TEMP%\ai_workflow_copilot_staging_handoff.md"

if not exist "%ENV_FILE%" (
  echo Missing %ENV_FILE%. Provide a valid env file path.
  exit /b 1
)

for /f "usebackq tokens=1,* delims==" %%A in (`findstr /R "^[A-Za-z_][A-Za-z0-9_]*=" "%ENV_FILE%"`) do (
  if /I "%%A"=="NEXT_PUBLIC_API_BASE_URL" set "API_BASE_URL=%%B"
  if /I "%%A"=="STAGING_WEB_URL" set "WEB_URL=%%B"
)

if not defined API_BASE_URL (
  set "HEALTH_URL=unknown"
  set "WEB_URL=unknown"
) else (
  if not defined WEB_URL set "WEB_URL=!API_BASE_URL:/api/v1=!"
  set "HEALTH_URL=!API_BASE_URL!/health"
)

for /f %%I in ('git rev-parse --short HEAD 2^>nul') do set "CHANGE_REF=%%I"
if not defined CHANGE_REF set "CHANGE_REF=unknown"

for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Get-Date -Format o"`) do set "REHEARSAL_AT=%%I"
if not defined REHEARSAL_AT set "REHEARSAL_AT=unknown"

set "RELEASE_OWNER=%USERNAME%"
if not defined RELEASE_OWNER set "RELEASE_OWNER=unknown"

(
  echo # Stage B Staging Release Evidence
  echo.
  echo ## Evidence Metadata
  echo.
  echo - Completed At: !REHEARSAL_AT!
  echo - Release Owner: !RELEASE_OWNER!
  echo - Env File: %ENV_FILE%
  echo - Service Mode: %SERVICE_MODE%
  echo - Change Ref: %CHANGE_REF%
  echo - Rollback Target: %ROLLBACK_TARGET%
  echo - Companion Handoff File: %HANDOFF_FILE%
  echo.
  echo ## Automated Routine Captured
  echo.
  echo - `scripts\release-check-windows.cmd %ENV_FILE%`
  echo - `docker compose --env-file %ENV_FILE% config`
  if /I "%SERVICE_MODE%"=="full-stack" (
    echo - `docker compose --env-file %ENV_FILE% up -d --build`
  ) else (
    echo - `docker compose --env-file %ENV_FILE% up -d --build server worker web`
  )
  echo - `scripts\migrate-windows.cmd %ENV_FILE%`
  echo - `docker compose --env-file %ENV_FILE% up -d --build --force-recreate server worker web`
  echo - `scripts\staging-smoke-windows.cmd %ENV_FILE%`
  echo.
  echo ## Verified Targets
  echo.
  echo - API Health URL: !HEALTH_URL!
  echo - Web Root URL: !WEB_URL!
  echo.
  echo ## Manual Smoke Record
  echo.
  echo - [ ] login succeeds
  echo - [ ] a workspace loads
  echo - [ ] the documents view loads without server errors
  echo - [ ] a Research task can run to completion
  echo - [ ] the formal Research report path can complete
  echo - [ ] traces and task history remain visible after the run
  echo.
  echo ## Evidence Notes
  echo.
  echo - What changed:
  echo - What was verified beyond the automated checks:
  echo - Anything unusual observed:
  echo - Follow-up needed before wider use:
) > "%EVIDENCE_FILE%"

echo Stage B release evidence written to %EVIDENCE_FILE%.
exit /b 0

:usage
echo Usage: scripts\write-release-evidence-windows.cmd [env-file] [rollback-target] [service-mode] [evidence-file] [handoff-file]
echo Writes a Stage B release evidence record with the selected env file, rollback target, and companion handoff path.
echo Defaults to .env.staging, app-tier, and %%TEMP%% output files when optional arguments are omitted.