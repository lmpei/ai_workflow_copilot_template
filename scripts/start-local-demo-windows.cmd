@echo off
setlocal

pushd "%~dp0.." || exit /b 1

if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo Created .env from .env.example
  echo Edit .env and replace AUTH_SECRET_KEY before the first run.
  popd
  exit /b 1
)

findstr /b /c:"AUTH_SECRET_KEY=replace_me" ".env" >nul
if not errorlevel 1 (
  echo AUTH_SECRET_KEY is still replace_me.
  echo Edit .env and set a unique secret before startup.
  popd
  exit /b 1
)

call "scripts\setup-windows.cmd" || (
  popd
  exit /b 1
)

docker compose up --build
set "exit_code=%ERRORLEVEL%"

popd
exit /b %exit_code%