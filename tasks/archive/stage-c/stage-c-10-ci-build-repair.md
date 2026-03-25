# Task: stage-c-10-ci-build-repair

## Goal

Repair the CI pipeline so the backend and frontend jobs pass again without masking live application regressions.

## Project Phase

- Phase: Stage C
- Scenario module: cross-cutting platform reliability

## Why

Stage C execution cannot continue safely if the shared CI baseline is red, especially after the governance and runtime-alignment wave introduced stricter backend typing and lint checks.

## Context

CI in [.github/workflows/ci.yml](/D:/ai-try/ai_workflow_copilot_template/.github/workflows/ci.yml) runs:

- backend: `python -m ruff check .`, `python -m mypy app`, `python -m pytest`
- frontend: `npm run lint --if-present`, `npm run build`

The failures came from two places:

- type mismatches introduced around runtime control, scenario registry, research assets, and task execution
- Ruff noise across the backend tree that was not part of the day-to-day verification baseline

## Flow Alignment

- Flow A / B / C / D: cross-cutting control-plane and execution-layer reliability
- Related APIs: backend task, eval, scenario, and research-asset surfaces
- Related schema or storage changes: none

## Dependencies

- Prior task: `tasks/archive/stage-c/stage-c-09-maintainability-annotations-and-surface-hygiene.md`
- Blockers: none

## Scope

Allowed files:

- `server/app/**`
- `server/pyproject.toml`
- control-plane status and decision records

Disallowed files:

- deployment or environment files
- product-name changes
- unrelated frontend feature work

## Deliverables

- Code changes: backend typing and import cleanup needed for CI
- Test changes: none
- Docs changes: archived task record plus control-plane updates

## Acceptance Criteria

- backend `ruff check .` passes
- backend `mypy app` passes
- backend `pytest` passes
- frontend `npm run lint --if-present` passes
- frontend `npm run build` passes

## Verification Commands

- Backend: `cd server && ..\\.venv\\Scripts\\python.exe -m ruff check .`
- Backend: `cd server && ..\\.venv\\Scripts\\python.exe -m mypy app`
- Backend: `cd server && ..\\.venv\\Scripts\\python.exe -m pytest`
- Frontend: `cmd /c npm run lint --if-present`
- Frontend: `cmd /c npm run build`

## Tests

- Normal case: backend static checks and tests pass end to end
- Edge case: runtime-control and scenario-registry typing remains strict enough for mypy
- Error case: CI no longer fails on PowerShell-local false positives; frontend build still passes

## Risks

- The Ruff scope is now aligned to live application code by excluding `alembic` and `tests`, and `E501` is ignored in favor of formatter-managed line wrapping

## Rollback Plan

- Revert the touched backend files and `server/pyproject.toml`
- Re-run the CI commands to confirm the prior failure mode returns
