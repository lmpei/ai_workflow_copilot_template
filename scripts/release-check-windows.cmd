@echo off
setlocal

if not exist ".env" (
  echo Missing .env. Copy .env.example to .env and fill live settings first.
  exit /b 1
)

findstr /R /C:"=replace_me$" .env >nul
if %ERRORLEVEL% EQU 0 (
  echo .env still contains replace_me. Replace placeholders or clear unused keys before release.
  exit /b 1
)

call scripts\verify-windows.cmd || exit /b 1

echo Stage A release preflight passed.
