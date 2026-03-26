@echo off
setlocal EnableExtensions EnableDelayedExpansion

if /I "%~1"=="--help" goto usage

set "ENV_FILE=%~1"
if "%ENV_FILE%"=="" set "ENV_FILE=.env.public-demo"

set "SERVICE_MODE=%~2"
if "%SERVICE_MODE%"=="" set "SERVICE_MODE=full-stack"

if /I not "%SERVICE_MODE%"=="app-tier" if /I not "%SERVICE_MODE%"=="full-stack" (
  echo Unsupported service mode %SERVICE_MODE%. Use app-tier or full-stack.
  exit /b 1
)

if not exist "%ENV_FILE%" (
  echo Missing %ENV_FILE%. Provide a valid env file path.
  exit /b 1
)

for %%I in ("%ENV_FILE%") do set "ENV_FILE_BASENAME=%%~nxI"

for /f "usebackq tokens=1,* delims==" %%A in (`findstr /R "^[A-Za-z_][A-Za-z0-9_]*=" "%ENV_FILE%"`) do (
  if /I "%%A"=="APP_ENV_FILE" set "APP_ENV_FILE_VALUE=%%B"
  if /I "%%A"=="PUBLIC_DEMO_MODE" set "PUBLIC_DEMO_MODE=%%B"
  if /I "%%A"=="NEXT_PUBLIC_API_BASE_URL" set "API_BASE_URL=%%B"
  if /I "%%A"=="PUBLIC_WEB_URL" set "PUBLIC_WEB_URL=%%B"
  if /I "%%A"=="PUBLIC_WEB_HOST" set "PUBLIC_WEB_HOST=%%B"
  if /I "%%A"=="PUBLIC_API_HOST" set "PUBLIC_API_HOST=%%B"
)

if "%APP_ENV_FILE_VALUE%"=="" (
  echo %ENV_FILE% does not define APP_ENV_FILE.
  exit /b 1
)

if /I not "%APP_ENV_FILE_VALUE%"=="%ENV_FILE%" if /I not "%APP_ENV_FILE_VALUE%"=="%ENV_FILE_BASENAME%" (
  echo APP_ENV_FILE=%APP_ENV_FILE_VALUE% does not match the selected env file %ENV_FILE%.
  exit /b 1
)

if /I not "%PUBLIC_DEMO_MODE%"=="true" (
  echo %ENV_FILE% must set PUBLIC_DEMO_MODE=true for the public demo deployment path.
  exit /b 1
)

if "%API_BASE_URL%"=="" (
  echo %ENV_FILE% does not define NEXT_PUBLIC_API_BASE_URL.
  exit /b 1
)

if "%PUBLIC_WEB_URL%"=="" (
  echo %ENV_FILE% does not define PUBLIC_WEB_URL.
  exit /b 1
)

if "%PUBLIC_WEB_HOST%"=="" (
  echo %ENV_FILE% does not define PUBLIC_WEB_HOST.
  exit /b 1
)

if "%PUBLIC_API_HOST%"=="" (
  echo %ENV_FILE% does not define PUBLIC_API_HOST.
  exit /b 1
)

call scripts\release-check-windows.cmd "%ENV_FILE%" || exit /b 1

set "COMPOSE_FILE=docker-compose.public-demo.yml"
docker compose --env-file "%ENV_FILE%" config >nul || exit /b 1

if /I "%SERVICE_MODE%"=="full-stack" (
  docker compose --env-file "%ENV_FILE%" up -d --build || exit /b 1
) else (
  docker compose --env-file "%ENV_FILE%" up -d --build server worker web reverse-proxy || exit /b 1
)

call scripts\migrate-windows.cmd "%ENV_FILE%" || exit /b 1
docker compose --env-file "%ENV_FILE%" up -d --build --force-recreate server worker web reverse-proxy || exit /b 1
call scripts\public-demo-smoke-windows.cmd "%ENV_FILE%" || exit /b 1

echo Public demo deployment path passed for %ENV_FILE%.
echo Compose file: %COMPOSE_FILE%
echo Service mode: %SERVICE_MODE%
exit /b 0

:usage
echo Usage: scripts\public-demo-deploy-windows.cmd [env-file] [service-mode]
echo Uses docker-compose.public-demo.yml to run the bounded public-demo deployment path.
echo Service mode defaults to full-stack and can be app-tier or full-stack.
echo The selected env file must define APP_ENV_FILE, PUBLIC_DEMO_MODE, NEXT_PUBLIC_API_BASE_URL, PUBLIC_WEB_URL, PUBLIC_WEB_HOST, and PUBLIC_API_HOST.
