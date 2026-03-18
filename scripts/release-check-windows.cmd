@echo off
setlocal

if /I "%~1"=="--help" goto usage

set "ENV_FILE=%~1"
if "%ENV_FILE%"=="" set "ENV_FILE=.env"

if not exist "%ENV_FILE%" (
  echo Missing %ENV_FILE%. Copy .env.example and fill live settings first.
  exit /b 1
)

findstr /R /C:"=replace_me$" "%ENV_FILE%" >nul
if %ERRORLEVEL% EQU 0 (
  echo %ENV_FILE% still contains replace_me. Replace placeholders or clear unused keys before release.
  exit /b 1
)

call scripts\verify-windows.cmd || exit /b 1

echo Stage A release preflight passed for %ENV_FILE%.
exit /b 0

:usage
echo Usage: scripts\release-check-windows.cmd [env-file]
echo Verifies the provided env file has no replace_me placeholders and then runs the repository verification baseline.
echo Defaults to .env when no env file is provided.
