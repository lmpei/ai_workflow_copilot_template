# Task: stage-a-07-research-iteration-workflow

## Goal

Turn the current Research report flow into an iterative workflow that can continue from prior research results instead
of always starting from a blank task.

## Project Stage

- Stage: Stage A
- Track: Research

## Why

Stage A cannot end with one-shot report generation. Research depth requires the user to refine, extend, and continue a
topic across multiple runs while preserving enough context to make follow-up work useful and trustworthy.

## Context

Relevant documents:

- `docs/prd/STAGE_A_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `docs/PROJECT_GUIDE.md`

Relevant runtime areas:

- `server/app/schemas/research.py`
- `server/app/services/research_assistant_service.py`
- `server/app/services/agent_service.py`
- `server/app/services/task_execution_service.py`
- `server/tests/`
- `web/lib/types.ts`
- `web/components/research/`
- `web/components/tasks/`

## Flow Alignment

- Flow A / B / C / D: Flow B / C / D
- Related APIs: tasks, workspaces, research module surfaces
- Related schema or storage changes: research follow-up input contract and research-result lineage metadata

## Dependencies

- Prior task: `tasks/archive/stage-a/stage-a-06-wave-two-planning.md`
- Blockers: none

## Scope

Allowed files:

- `server/app/schemas/`
- `server/app/services/`
- `server/app/repositories/`
- `server/tests/`
- `web/lib/`
- `web/components/research/`
- `web/components/tasks/`
- `docs/PROJECT_GUIDE.md`

Disallowed files:

- support or job module surfaces
- deployment/operations docs unrelated to Research workflow behavior

## Deliverables

- Code changes:
  - define a follow-up Research input path that can reference prior results or reports
  - preserve lineage metadata between an original research run and its continuation
  - update the Research surface so a user can continue or refine an existing research result
- Test changes:
  - add or update regression coverage for follow-up Research execution and result lineage
- Docs changes:
  - update the Research workflow guide if the canonical continuation contract changes developer expectations

## Acceptance Criteria

- a user can launch a follow-up Research task from an existing Research result or report
- the follow-up task preserves enough prior context to support refinement rather than starting from zero
- result lineage is explicit enough for later eval and trace work
- the existing Stage A report flow remains stable for first-run Research tasks

## Verification Commands

- Backend:
  - `python -m compileall server/app server/tests`
  - `cd server`
  - `..\.venv\Scripts\python.exe -m pytest tests/test_research_assistant_service.py tests/test_tasks.py tests/test_agent_service.py tests/test_task_execution_service.py`
- Frontend:
  - `cmd /c npm --prefix web run verify`

## Tests

- Normal case:
  - a formal Research report can be continued into a follow-up task with preserved intent and evidence context
- Edge case:
  - a follow-up run can narrow or extend scope without breaking the base report shape
- Error case:
  - invalid or missing parent Research references are rejected clearly

## Risks

- over-coupling iteration flow to specific UI assumptions instead of keeping the underlying Research contract reusable

## Rollback Plan

- revert the follow-up Research contract and surface changes while keeping the current Stage A report flow intact
