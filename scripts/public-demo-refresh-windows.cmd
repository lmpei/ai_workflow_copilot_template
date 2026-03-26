@echo off
setlocal EnableExtensions EnableDelayedExpansion

if /I "%~1"=="--help" goto usage

set "ENV_FILE=%~1"
if "%ENV_FILE%"=="" set "ENV_FILE=.env"

set "SERVICE_MODE=%~2"
if "%SERVICE_MODE%"=="" set "SERVICE_MODE=app-tier"

if /I not "%SERVICE_MODE%"=="app-tier" if /I not "%SERVICE_MODE%"=="full-stack" (
  echo Unsupported service mode %SERVICE_MODE%. Use app-tier or full-stack.
  exit /b 1
)

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
call scripts\public-demo-smoke-windows.cmd "%ENV_FILE%" || exit /b 1

echo Public demo refresh routine passed for %ENV_FILE%.
echo.
echo Next operator steps:
echo - sign in with a reserved operator account or a fresh demo account
echo - create a guided demo workspace from the Workspace Hub if you need a clean showcase path
echo - if account workspace slots are exhausted, use a fresh demo account or reset the environment outside this repo's bounded automation
exit /b 0

:usage
echo Usage: scripts\public-demo-refresh-windows.cmd [env-file] [service-mode]
echo Runs bounded public-demo preflight, compose config validation, startup, migration, force-recreate, and public-demo smoke checks.
echo Service mode defaults to app-tier and can be app-tier or full-stack.
echo Defaults to .env when no env file is provided.