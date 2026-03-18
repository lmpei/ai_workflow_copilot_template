# Task: stage-b-03-recoverable-runtime-and-control-actions

## Goal

Add clearer recovery and control semantics for Stage B tasks and evals.

## Project Stage

- Stage: Stage B
- Track: Platform Reliability

## Why

Stage A added trust baselines, traces, and stronger failure shapes, but long-running work still lacks a richer recovery
model. Stage B should make interrupted or operator-controlled work easier to understand and safer to recover.

## Context

Relevant documents:

- `docs/prd/STAGE_B_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `docs/PROJECT_GUIDE.md`

Relevant runtime areas:

- `server/app/services/task_execution_service.py`
- `server/app/services/eval_execution_service.py`
- `server/app/repositories/`
- `server/app/models/`
- `server/app/schemas/`
- `server/app/api/routes/`
- `server/tests/`

## Flow Alignment

- Flow A / B / C / D: Flow C / D with support for Flow B recovery visibility
- Related APIs: tasks, evals, traces, metrics
- Related schema or storage changes: recovery-state and control-action fields as needed

## Dependencies

- Prior task: `tasks/archive/stage-b/stage-b-01-task-stack-planning.md`
- Blockers: none

## Scope

Allowed files:

- `server/app/services/`
- `server/app/repositories/`
- `server/app/models/`
- `server/app/schemas/`
- `server/app/api/routes/`
- `server/tests/`
- `docs/PROJECT_GUIDE.md`

Disallowed files:

- unrelated frontend product work beyond any minimal control or status exposure needed
- deployment automation unrelated to runtime recovery

## Deliverables

- Code changes:
  - define Stage B recovery or control semantics such as cancel, retry, resume, or equivalent recovery-safe actions
  - make runtime state transitions and recovery traces clearer
  - preserve idempotency and failure-shape discipline while new control actions are added
- Test changes:
  - add or update recovery-oriented coverage for tasks and evals
- Docs changes:
  - document the recovery model if it changes developer expectations

## Acceptance Criteria

- interrupted or operator-controlled work is easier to understand and recover
- task and eval states expose clearer recovery intent than Stage A
- traces and persisted state remain trustworthy after recovery actions

## Verification Commands

- Backend:
  - `python -m compileall server/app server/tests`
  - `cd server`
  - `..\.venv\Scripts\python.exe -m pytest tests/test_task_execution_service.py tests/test_eval_execution_service.py tests/test_tasks.py tests/test_evals.py`

## Tests

- Normal case:
  - a recoverable task or eval follows the intended control path without duplicating unsafe side effects
- Edge case:
  - already terminal work rejects inappropriate recovery actions clearly
- Error case:
  - runtime interruptions still persist enough state for diagnosis and safe retry decisions

## Risks

- introducing recovery controls without strict state boundaries could create more ambiguity instead of less

## Rollback Plan

- revert the Stage B runtime-recovery changes while preserving the Stage A trust, trace, and failure-shape baseline
