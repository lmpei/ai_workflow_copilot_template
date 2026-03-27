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

set "EVIDENCE_FILE=%~4"
if "%EVIDENCE_FILE%"=="" set "EVIDENCE_FILE=%TEMP%\ai_workflow_copilot_public_demo_evidence.md"

set "HANDOFF_FILE=%~5"
if "%HANDOFF_FILE%"=="" set "HANDOFF_FILE=%TEMP%\ai_workflow_copilot_public_demo_handoff.md"

if not exist "%ENV_FILE%" (
  echo Missing %ENV_FILE%. Provide a valid env file path.
  exit /b 1
)

for /f "usebackq tokens=1,* delims==" %%A in (`findstr /R "^[A-Za-z_][A-Za-z0-9_]*=" "%ENV_FILE%"`) do (
  if /I "%%A"=="NEXT_PUBLIC_API_BASE_URL" set "API_BASE_URL=%%B"
  if /I "%%A"=="PUBLIC_WEB_URL" set "WEB_URL=%%B"
)

if not defined API_BASE_URL set "API_BASE_URL=unknown"
if not defined WEB_URL set "WEB_URL=unknown"

set "HEALTH_URL=%API_BASE_URL%/health"
set "PUBLIC_DEMO_URL=%API_BASE_URL%/public-demo"
set "TEMPLATES_URL=%API_BASE_URL%/public-demo/templates"
set "LOGIN_URL=%WEB_URL%/login"
set "WORKSPACES_URL=%WEB_URL%/workspaces"

for /f %%I in ('git rev-parse --short HEAD 2^>nul') do set "CHANGE_REF=%%I"
if not defined CHANGE_REF set "CHANGE_REF=unknown"

for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Get-Date -Format o"`) do set "REHEARSAL_AT=%%I"
if not defined REHEARSAL_AT set "REHEARSAL_AT=unknown"

set "OPERATOR=%USERNAME%"
if not defined OPERATOR set "OPERATOR=unknown"

(
  echo # Stage D Public Demo Rollout Evidence
  echo.
  echo ## Evidence Metadata
  echo.
  echo - Completed At: !REHEARSAL_AT!
  echo - Operator: !OPERATOR!
  echo - Env File: %ENV_FILE%
  echo - Service Mode: %SERVICE_MODE%
  echo - Change Ref: %CHANGE_REF%
  echo - Rollback Target: %ROLLBACK_TARGET%
  echo - Public Web URL: %WEB_URL%
  echo - Public API Base URL: %API_BASE_URL%
  echo - Companion Handoff File: %HANDOFF_FILE%
  echo.
  echo ## Automated Routine Captured
  echo.
  echo - `scripts\release-check-windows.cmd %ENV_FILE%`
  echo - `scripts\public-demo-deploy-windows.cmd %ENV_FILE% %SERVICE_MODE%`
  echo - `scripts\public-demo-smoke-windows.cmd %ENV_FILE%`
  echo.
  echo ## Verified Targets
  echo.
  echo - API Health URL: !HEALTH_URL!
  echo - Public Demo Settings URL: !PUBLIC_DEMO_URL!
  echo - Public Demo Templates URL: !TEMPLATES_URL!
  echo - Web Root URL: %WEB_URL%
  echo - Login URL: !LOGIN_URL!
  echo - Workspace URL: !WORKSPACES_URL!
  echo.
  echo ## Manual Smoke Record
  echo.
  echo - [ ] login succeeds
  echo - [ ] `Workspace Hub` loads
  echo - [ ] guided demo workspace creation succeeds
  echo - [ ] the seeded workspace overview shows the guided showcase panel
  echo - [ ] one seeded path reaches `Documents -^> Chat -^> Tasks`
  echo.
  echo ## External Prerequisites Used
  echo.
  echo - VM host:
  echo - DNS / TLS status:
  echo - Env file location:
  echo.
  echo ## Evidence Notes
  echo.
  echo - What was launched:
  echo - Which automated checks passed:
  echo - Which manual checks passed:
  echo - Anything unusual observed:
  echo - Follow-up needed before wider sharing:
) > "%EVIDENCE_FILE%"

echo Stage D public demo rollout evidence written to %EVIDENCE_FILE%.
exit /b 0

:usage
echo Usage: scripts\write-public-demo-rollout-evidence-windows.cmd [env-file] [rollback-target] [service-mode] [evidence-file] [handoff-file]
echo Writes a Stage D public-demo rollout evidence record with the selected env file, rollback target, and companion handoff path.
echo Defaults to .env.public-demo, full-stack, and %%TEMP%% output files when optional arguments are omitted.
