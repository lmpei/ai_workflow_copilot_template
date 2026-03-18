@echo off
setlocal EnableExtensions EnableDelayedExpansion

if /I "%~1"=="--help" goto usage

set "ENV_FILE=%~1"
if "%ENV_FILE%"=="" set "ENV_FILE=.env"

if not exist "%ENV_FILE%" (
  echo Missing %ENV_FILE%. Copy .env.example and fill live settings first.
  exit /b 1
)

for %%I in ("%ENV_FILE%") do set "ENV_FILE_BASENAME=%%~nxI"
for /f "usebackq tokens=1,* delims==" %%A in (`findstr /R "^[A-Za-z_][A-Za-z0-9_]*=" "%ENV_FILE%"`) do (
  if /I "%%A"=="APP_ENV_FILE" set "APP_ENV_FILE_VALUE=%%B"
)

if "!APP_ENV_FILE_VALUE!"=="" (
  echo %ENV_FILE% does not define APP_ENV_FILE. Set it to the selected env file path.
  exit /b 1
)

if /I not "!APP_ENV_FILE_VALUE!"=="%ENV_FILE%" if /I not "!APP_ENV_FILE_VALUE!"=="!ENV_FILE_BASENAME!" (
  echo APP_ENV_FILE=!APP_ENV_FILE_VALUE! does not match the selected env file %ENV_FILE%.
  exit /b 1
)

findstr /R /C:"=replace_me$" "%ENV_FILE%" >nul
if %ERRORLEVEL% EQU 0 (
  echo %ENV_FILE% still contains replace_me. Replace placeholders or clear unused keys before release.
  exit /b 1
)

call scripts\verify-windows.cmd || exit /b 1

echo Release preflight passed for %ENV_FILE%.
exit /b 0

:usage
echo Usage: scripts\release-check-windows.cmd [env-file]
echo Verifies APP_ENV_FILE alignment, rejects replace_me placeholders, and then runs the repository verification baseline.
echo Defaults to .env when no env file is provided.
