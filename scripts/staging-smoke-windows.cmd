@echo off
setlocal

if /I "%~1"=="--help" goto usage

set "ENV_FILE=%~1"
if "%ENV_FILE%"=="" set "ENV_FILE=.env"

if not exist "%ENV_FILE%" (
  echo Missing %ENV_FILE%. Provide a valid env file path.
  exit /b 1
)

for /f "usebackq tokens=1,* delims==" %%A in (`findstr /R "^[A-Za-z_][A-Za-z0-9_]*=" "%ENV_FILE%"`) do (
  if /I "%%A"=="NEXT_PUBLIC_API_BASE_URL" set "API_BASE_URL=%%B"
  if /I "%%A"=="STAGING_WEB_URL" set "WEB_URL=%%B"
)

if "%API_BASE_URL%"=="" (
  echo %ENV_FILE% does not define NEXT_PUBLIC_API_BASE_URL.
  exit /b 1
)

if "%WEB_URL%"=="" set "WEB_URL=%API_BASE_URL:/api/v1=%"
set "HEALTH_URL=%API_BASE_URL%/health"

curl.exe -fsS "%HEALTH_URL%" >nul || (
  echo API health check failed for %HEALTH_URL%.
  exit /b 1
)

curl.exe -fsS "%WEB_URL%" >nul || (
  echo Web root check failed for %WEB_URL%.
  exit /b 1
)

echo Staging smoke passed for %ENV_FILE%.
echo API health: %HEALTH_URL%
echo Web root: %WEB_URL%
exit /b 0

:usage
echo Usage: scripts\staging-smoke-windows.cmd [env-file]
echo Checks the API health endpoint and web root derived from the provided env file.
echo Defaults to .env when no env file is provided.
