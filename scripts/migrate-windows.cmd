@echo off
setlocal EnableExtensions EnableDelayedExpansion

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

echo %DATABASE_URL% | findstr /I /C:"@db:" >nul
if %ERRORLEVEL% EQU 0 goto compose_migration

if not exist ".\.venv\Scripts\python.exe" (
  echo Missing .venv\Scripts\python.exe. Run scripts\setup-windows.cmd first.
  exit /b 1
)

pushd server || exit /b 1
for /f %%I in ('"..\.venv\Scripts\python.exe" -m app.core.alembic_bootstrap') do set "STAMP_REVISION=%%I"
if defined STAMP_REVISION (
  call "..\.venv\Scripts\python.exe" -m alembic stamp !STAMP_REVISION! || (
    popd
    exit /b 1
  )
)
call "..\.venv\Scripts\python.exe" -m alembic upgrade head || (
  popd
  exit /b 1
)
popd

echo Database migrations applied.
exit /b 0

:compose_migration
for /f %%I in ('docker compose --env-file "%ENV_FILE%" ps -q server 2^>nul') do set "SERVER_CONTAINER=%%I"

if defined SERVER_CONTAINER (
  for /f %%I in ('docker compose --env-file "%ENV_FILE%" exec -T server python -m app.core.alembic_bootstrap') do set "STAMP_REVISION=%%I"
  if defined STAMP_REVISION (
    docker compose --env-file "%ENV_FILE%" exec -T server python -m alembic stamp !STAMP_REVISION! || exit /b 1
  )
  docker compose --env-file "%ENV_FILE%" exec -T server python -m alembic upgrade head || exit /b 1
) else (
  for /f %%I in ('docker compose --env-file "%ENV_FILE%" run --rm --no-deps server python -m app.core.alembic_bootstrap') do set "STAMP_REVISION=%%I"
  if defined STAMP_REVISION (
    docker compose --env-file "%ENV_FILE%" run --rm --no-deps server python -m alembic stamp !STAMP_REVISION! || exit /b 1
  )
  docker compose --env-file "%ENV_FILE%" run --rm --no-deps server python -m alembic upgrade head || exit /b 1
)

echo Database migrations applied through the server container.
exit /b 0

:usage
echo Usage: scripts\migrate-windows.cmd [env-file]
echo Applies Alembic migrations using DATABASE_URL from the provided env file.
echo Uses Docker Compose when DATABASE_URL targets the local Compose db hostname.
echo Automatically stamps legacy pre-versioned databases before upgrade when needed.
echo Defaults to .env when no env file is provided.
