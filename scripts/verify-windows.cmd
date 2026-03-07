@echo off
setlocal

pushd server || exit /b 1
call "..\.venv\Scripts\python.exe" -m ruff check . || (
  popd
  exit /b 1
)
call "..\.venv\Scripts\python.exe" -m mypy app || (
  popd
  exit /b 1
)
call "..\.venv\Scripts\python.exe" -m pytest || (
  popd
  exit /b 1
)
popd

pushd web || exit /b 1
call npm.cmd run verify || (
  popd
  exit /b 1
)
popd

echo Windows verification passed.
