# Task: stage-c-03-job-assistant-structured-hiring-workflow

## Goal

Turn Job Assistant from a runnable skeleton into a clearer structured hiring workflow with stronger task inputs,
match outputs, and review surfaces.

## Project Stage

- Stage: Stage C
- Track: Research reference workflow applied to Job Assistant

## Why

The platform should prove that structured workflow depth can extend into hiring use cases as well as Research.
Job Assistant already runs end to end on shared primitives, but it still presents a thinner workflow than the Research
reference surface.

## Context

Relevant documents:

- `docs/prd/STAGE_C_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `docs/PROJECT_GUIDE.md`
- `server/app/schemas/job.py`
- `server/app/services/job_assistant_service.py`
- `web/components/job/job-assistant-panel.tsx`

## Flow Alignment

- Flow A / B / C / D: Job workflows on the shared platform core
- Related APIs: workspace task APIs
- Related schema or storage changes: Job task contracts and results only if needed

## Dependencies

- Prior task: `tasks/archive/stage-c/stage-c-01-task-stack-planning.md`
- Blockers: none

## Scope

Allowed files:

- `server/app/schemas/`
- `server/app/services/`
- `server/app/api/routes/` if contract exposure changes are needed
- `server/tests/`
- `web/components/job/`
- `web/lib/`
- `docs/PROJECT_GUIDE.md`
- `STATUS.md`

Disallowed files:

- unrelated Research workbench changes
- unrelated delivery-script work

## Deliverables

- Code changes:
  - deepen Job task input/output contracts and structured hiring result shape
  - improve the Job surface so the workflow is more than a thin launcher and result dump
- Docs changes:
  - capture the upgraded Job workflow shape in durable docs if the result contract changes

## Acceptance Criteria

- Job tasks remain runnable on the shared task runtime
- Job results are more structured and reviewer-readable than the current skeleton baseline
- the UI makes the hiring workflow feel intentionally structured, not placeholder-level

## Verification Commands

- Backend:
  - `cd server`
  - `..\\.venv\\Scripts\\python.exe -m pytest tests/test_tasks.py tests/test_agent_service.py`
- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - a job workspace can launch and inspect the upgraded structured hiring workflow
- Edge case:
  - limited hiring context still produces an honest degraded output instead of pretending strong fit evidence exists
- Error case:
  - invalid Job contract input fails cleanly without breaking the shared task runtime

## Risks

- treating Job Assistant like a copy of Research could blur the role-fit workflow into generic summarization

## Rollback Plan

- revert the Job workflow deepening while preserving the broader Stage C planning boundary