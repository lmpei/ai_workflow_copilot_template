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

set "HANDOFF_FILE=%~4"
if "%HANDOFF_FILE%"=="" set "HANDOFF_FILE=%TEMP%\ai_workflow_copilot_staging_handoff.md"

set "EVIDENCE_FILE=%~5"
if "%EVIDENCE_FILE%"=="" set "EVIDENCE_FILE=%TEMP%\ai_workflow_copilot_staging_evidence.md"

if not exist "%ENV_FILE%" (
  echo Missing %ENV_FILE%. Provide a valid env file path.
  exit /b 1
)

call scripts\release-check-windows.cmd "%ENV_FILE%" || exit /b 1
docker compose --env-file "%ENV_FILE%" config >nul || exit /b 1

if /I "%SERVICE_MODE%"=="full-stack" (
  docker compose --env-file "%ENV_FILE%" up -d --build || exit /b 1
) else (
  docker compose --env-file "%ENV_FILE%" up -d --build server worker web || exit /b 1
)

call scripts\migrate-windows.cmd "%ENV_FILE%" || exit /b 1
docker compose --env-file "%ENV_FILE%" up -d --build --force-recreate server worker web || exit /b 1
call scripts\staging-smoke-windows.cmd "%ENV_FILE%" || exit /b 1
call scripts\write-release-evidence-windows.cmd "%ENV_FILE%" "%ROLLBACK_TARGET%" "%SERVICE_MODE%" "%EVIDENCE_FILE%" "%HANDOFF_FILE%" || exit /b 1

for /f %%I in ('git rev-parse --short HEAD 2^>nul') do set "CHANGE_REF=%%I"
if not defined CHANGE_REF set "CHANGE_REF=unknown"

for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Get-Date -Format o"`) do set "REHEARSAL_AT=%%I"

(
  echo # Stage B Staging Rehearsal Handoff
  echo.
  echo ## Rehearsal Metadata
  echo.
  echo - Completed At: !REHEARSAL_AT!
  echo - Env File: %ENV_FILE%
  echo - Service Mode: %SERVICE_MODE%
  echo - Change Ref: %CHANGE_REF%
  echo - Rollback Target: %ROLLBACK_TARGET%
  echo - Evidence File: %EVIDENCE_FILE%
  echo.
  echo ## Automated Steps Completed
  echo.
  echo - `scripts\release-check-windows.cmd %ENV_FILE%`
  if /I "%SERVICE_MODE%"=="full-stack" (
    echo - `docker compose --env-file %ENV_FILE% up -d --build`
  ) else (
    echo - `docker compose --env-file %ENV_FILE% up -d --build server worker web`
  )
  echo - `scripts\migrate-windows.cmd %ENV_FILE%`
  echo - `docker compose --env-file %ENV_FILE% up -d --build --force-recreate server worker web`
  echo - `scripts\staging-smoke-windows.cmd %ENV_FILE%`
  echo.
  echo ## Manual Smoke Still Required
  echo.
  echo - login succeeds
  echo - a workspace loads
  echo - the documents view loads without server errors
  echo - a Research task can run to completion
  echo - the formal Research report path can complete
  echo - traces and task history remain visible after the run
  echo.
  echo ## Handoff Notes
  echo.
  echo - What changed:
  echo - Anything unusual observed:
  echo - Follow-up needed before wider use:
) > "%HANDOFF_FILE%"

echo Stage B staging rehearsal passed for %ENV_FILE%.
echo Release evidence written to %EVIDENCE_FILE%.
echo Handoff note written to %HANDOFF_FILE%.
exit /b 0

:usage
echo Usage: scripts\staging-rehearse-windows.cmd [env-file] [rollback-target] [service-mode] [handoff-file] [evidence-file]
echo Runs Stage B staging preflight, compose config validation, startup, migration, force-recreate, and smoke checks.
echo Service mode defaults to app-tier and can be app-tier or full-stack.
echo The handoff note defaults to %%TEMP%%\ai_workflow_copilot_staging_handoff.md.
echo The release evidence record defaults to %%TEMP%%\ai_workflow_copilot_staging_evidence.md.