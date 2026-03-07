@echo off
setlocal

if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo Created .env from .env.example
)

if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv || exit /b 1
)

".\.venv\Scripts\python.exe" -m pip install -r server\requirements.txt || exit /b 1

pushd web || exit /b 1
call npm.cmd ci || (
  popd
  exit /b 1
)
popd

echo Windows setup completed.
