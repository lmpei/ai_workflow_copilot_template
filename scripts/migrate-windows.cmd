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
  if /I "%%A"=="DATABASE_URL" set "DATABASE_URL=%%B"
)

if "%DATABASE_URL%"=="" (
  echo %ENV_FILE% does not define DATABASE_URL.
  exit /b 1
)

if not exist ".\.venv\Scripts\python.exe" (
  echo Missing .venv\Scripts\python.exe. Run scripts\setup-windows.cmd first.
  exit /b 1
)

pushd server || exit /b 1
call "..\.venv\Scripts\python.exe" -m alembic upgrade head || (
  popd
  exit /b 1
)
popd

echo Database migrations applied.
exit /b 0

:usage
echo Usage: scripts\migrate-windows.cmd [env-file]
echo Applies Alembic migrations using DATABASE_URL from the provided env file.
echo Defaults to .env when no env file is provided.
