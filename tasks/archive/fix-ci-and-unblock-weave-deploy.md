# Task: Fix CI and Unblock Weave Deploy

## Goal

Clear the backend `ruff` failures that blocked the latest `CI` run so `Deploy Weave` can execute again on `main`.

## Context

The latest pushed commit reached `CI`, but the backend job failed on `python -m ruff check .`. Because production deploy is gated by successful upstream `CI`, `Deploy Weave` skipped the deploy job and the cloud server stayed on the older version.

## Scope

Allowed files:

- backend files needed to clear the current `ruff` failures
- `STATUS.md`
- task docs for this slice

Disallowed files:

- unrelated product behavior changes
- deployment workflow changes
- environment or server config changes

## Acceptance Criteria

- local backend `ruff` passes
- backend regression still passes
- changes are committed and pushed to `main`
- this task is archived and `STATUS.md` reflects completion

## Verification

- `cd server && ..\.venv\Scripts\python.exe -m ruff check .`
- `cd server && ..\.venv\Scripts\python.exe -m pytest tests`
