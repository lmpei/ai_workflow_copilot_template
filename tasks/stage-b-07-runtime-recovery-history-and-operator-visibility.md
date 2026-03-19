# Task: stage-b-07-runtime-recovery-history-and-operator-visibility

## Goal

Extend the Stage B runtime controls with clearer recovery history and operator-visible runtime state for tasks and eval
runs.

## Project Stage

- Stage: Stage B
- Track: Platform Reliability

## Why

Stage B wave one introduced persisted cancel and retry semantics, but operators still have limited visibility into how a
task or eval run arrived at its current recovery state. The next runtime wave should make recovery behavior easier to
inspect without claiming full checkpoint/resume support.

## Context

Relevant documents:

- `docs/prd/STAGE_B_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `docs/PROJECT_GUIDE.md`

Relevant runtime areas:

- `server/app/core/`
- `server/app/services/`
- `server/app/api/routes/`
- `server/app/models/`
- `server/app/schemas/`
- `server/tests/`
- `web/lib/`
- `web/components/`

## Flow Alignment

- Flow A / B / C / D: supports all flows that depend on task or eval execution
- Related APIs: tasks, eval runs, observability surfaces
- Related schema or storage changes: runtime control and recovery metadata only as needed

## Dependencies

- Prior task: `tasks/archive/stage-b/stage-b-05-wave-two-planning.md`
- Blockers: none

## Scope

Allowed files:

- `server/app/core/`
- `server/app/services/`
- `server/app/api/routes/`
- `server/app/models/`
- `server/app/schemas/`
- `server/tests/`
- `web/lib/`
- `web/components/`
- `docs/PROJECT_GUIDE.md`

Disallowed files:

- unsupported checkpoint/resume claims
- unrelated Research productization work

## Deliverables

- Code changes:
  - expose recovery history or operator-facing recovery details for tasks and eval runs
  - improve visibility into cancel and retry lineage where appropriate
- Test changes:
  - add or update coverage for runtime recovery history and operator-visible state
- Docs changes:
  - clarify what Stage B runtime recovery does and does not support

## Acceptance Criteria

- an operator can tell why a task or eval run is in its current recovery state
- retry and cancel lineage remain inspectable after the initial control action
- the runtime still does not overstate unsupported checkpoint/resume guarantees

## Verification Commands

- Backend:
  - `python -m compileall server/app server/tests`
  - `cd server`
  - `..\.venv\Scripts\python.exe -m pytest tests/test_runtime_control.py tests/test_tasks.py tests/test_evals.py tests/test_task_execution_service.py tests/test_eval_execution_service.py`
- Frontend:
  - `cmd /c npm --prefix web run verify`

## Tests

- Normal case:
  - a cancelled or retried task shows operator-visible recovery lineage
- Edge case:
  - repeated control actions preserve a coherent history instead of overwriting prior intent
- Error case:
  - unsupported control paths fail clearly without implying a resume capability that does not exist

## Risks

- exposing too much low-level recovery detail could create a misleading operator contract before the runtime model is stable

## Rollback Plan

- revert the recovery-history additions while preserving the Stage B cancel and retry control baseline
