@echo off
setlocal EnableExtensions EnableDelayedExpansion

if /I "%~1"=="--help" goto usage

set "ENV_FILE=%~1"
if "%ENV_FILE%"=="" set "ENV_FILE=.env.public-demo"

set "ROLLBACK_TARGET=%~2"
if "%ROLLBACK_TARGET%"=="" (
  echo Missing rollback target. Provide a prior image tag, commit, or release label.
  exit /b 1
)

set "SERVICE_MODE=%~3"
if "%SERVICE_MODE%"=="" set "SERVICE_MODE=full-stack"

if /I not "%SERVICE_MODE%"=="app-tier" if /I not "%SERVICE_MODE%"=="full-stack" (
  echo Unsupported service mode %SERVICE_MODE%. Use app-tier or full-stack.
  exit /b 1
)

set "HANDOFF_FILE=%~4"
if "%HANDOFF_FILE%"=="" set "HANDOFF_FILE=%TEMP%\ai_workflow_copilot_public_demo_handoff.md"

set "EVIDENCE_FILE=%~5"
if "%EVIDENCE_FILE%"=="" set "EVIDENCE_FILE=%TEMP%\ai_workflow_copilot_public_demo_evidence.md"

if not exist "%ENV_FILE%" (
  echo Missing %ENV_FILE%. Provide a valid env file path.
  exit /b 1
)

call scripts\public-demo-deploy-windows.cmd "%ENV_FILE%" "%SERVICE_MODE%" || exit /b 1
call scripts\write-public-demo-rollout-evidence-windows.cmd "%ENV_FILE%" "%ROLLBACK_TARGET%" "%SERVICE_MODE%" "%EVIDENCE_FILE%" "%HANDOFF_FILE%" || exit /b 1

for /f "usebackq tokens=1,* delims==" %%A in (`findstr /R "^[A-Za-z_][A-Za-z0-9_]*=" "%ENV_FILE%"`) do (
  if /I "%%A"=="NEXT_PUBLIC_API_BASE_URL" set "API_BASE_URL=%%B"
  if /I "%%A"=="PUBLIC_WEB_URL" set "WEB_URL=%%B"
)

if not defined API_BASE_URL set "API_BASE_URL=unknown"
if not defined WEB_URL set "WEB_URL=unknown"

for /f %%I in ('git rev-parse --short HEAD 2^>nul') do set "CHANGE_REF=%%I"
if not defined CHANGE_REF set "CHANGE_REF=unknown"

for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Get-Date -Format o"`) do set "REHEARSAL_AT=%%I"
if not defined REHEARSAL_AT set "REHEARSAL_AT=unknown"

set "OPERATOR=%USERNAME%"
if not defined OPERATOR set "OPERATOR=unknown"

(
  echo # Stage D Public Demo Rollout Handoff
  echo.
  echo ## Rehearsal Metadata
  echo.
  echo - Completed At: !REHEARSAL_AT!
  echo - Operator: !OPERATOR!
  echo - Env File: %ENV_FILE%
  echo - Service Mode: %SERVICE_MODE%
  echo - Change Ref: %CHANGE_REF%
  echo - Rollback Target: %ROLLBACK_TARGET%
  echo - Public Web URL: %WEB_URL%
  echo - Public API Base URL: %API_BASE_URL%
  echo - Evidence File: %EVIDENCE_FILE%
  echo.
  echo ## Automated Steps Completed
  echo.
  echo - `scripts\release-check-windows.cmd %ENV_FILE%`
  echo - `scripts\public-demo-deploy-windows.cmd %ENV_FILE% %SERVICE_MODE%`
  echo - `scripts\public-demo-smoke-windows.cmd %ENV_FILE%`
  echo.
  echo ## Manual Smoke Still Required
  echo.
  echo - login succeeds
  echo - `Workspace Hub` loads
  echo - guided demo workspace creation succeeds
  echo - the seeded workspace overview shows the guided showcase panel
  echo - one seeded path reaches `Documents -^> Chat -^> Tasks`
  echo.
  echo ## Handoff Notes
  echo.
  echo - What was launched:
  echo - What was verified beyond the automated checks:
  echo - Anything unusual observed:
  echo - Follow-up needed before wider sharing:
) > "%HANDOFF_FILE%"

echo Stage D public demo rollout rehearsal helper passed for %ENV_FILE%.
echo Release evidence written to %EVIDENCE_FILE%.
echo Handoff note written to %HANDOFF_FILE%.
exit /b 0

:usage
echo Usage: scripts\public-demo-rehearse-windows.cmd [env-file] [rollback-target] [service-mode] [handoff-file] [evidence-file]
echo Runs the bounded Stage D public-demo deployment path and writes rollout evidence plus a handoff note.
echo Service mode defaults to full-stack and can be app-tier or full-stack.
echo The handoff note defaults to %%TEMP%%\ai_workflow_copilot_public_demo_handoff.md.
echo The release evidence record defaults to %%TEMP%%\ai_workflow_copilot_public_demo_evidence.md.
