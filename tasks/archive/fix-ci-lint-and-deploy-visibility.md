# Task: Fix CI lint blockers and improve deploy visibility

## Goal

Clear the backend `ruff` failures that blocked `CI` for commit `85fbad4`, then make the deploy workflow expose whether deployment was skipped because upstream `CI` failed versus because deploy itself failed.

## Scope

- Fix current backend `ruff` violations so `CI` can pass again.
- Improve `.github/workflows/deploy-weave.yml` so `workflow_run` failures from `CI` are surfaced clearly in the deploy run summary.
- Update control-plane docs after the change is durable.

## Out of Scope

- Changing deploy strategy from `CI -> deploy` to unconditional deploy-on-push.
- Broad refactors unrelated to current `ruff` blockers.
- New alerting channels outside GitHub Actions summaries and logs.

## Verification

- `cd server`
- `..\.venv\Scripts\python.exe -m ruff check .`
- `..\.venv\Scripts\python.exe -m pytest tests`
- `npm --prefix web run verify`

## Completion Notes

- Archive this task under `tasks/archive/` once verification passes and control-plane docs are updated.
