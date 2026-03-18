@echo off
setlocal

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
