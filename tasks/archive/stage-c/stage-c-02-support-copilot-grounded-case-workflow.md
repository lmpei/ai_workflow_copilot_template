# Task: stage-c-02-support-copilot-grounded-case-workflow

## Goal

Turn Support Copilot from a runnable skeleton into a clearer grounded case workflow with stronger structured inputs,
outputs, and operator-facing UI.

## Project Stage

- Stage: Stage C
- Track: Research reference workflow applied to Support Copilot

## Why

The platform should prove that deeper workflow value is not limited to Research. Support Copilot already runs on the
shared platform core, but it still behaves like a thinner task surface than Research.

## Context

Relevant documents:

- `docs/prd/STAGE_C_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `docs/PROJECT_GUIDE.md`
- `server/app/schemas/support.py`
- `server/app/services/support_copilot_service.py`
- `web/components/support/support-copilot-panel.tsx`

## Flow Alignment

- Flow A / B / C / D: Support workflows on the shared platform core
- Related APIs: workspace task APIs
- Related schema or storage changes: Support task contracts and results only if needed

## Dependencies

- Prior task: `tasks/archive/stage-c/stage-c-01-task-stack-planning.md`
- Blockers: none

## Scope

Allowed files:

- `server/app/schemas/`
- `server/app/services/`
- `server/app/api/routes/` if contract exposure changes are needed
- `server/tests/`
- `web/components/support/`
- `web/lib/`
- `docs/PROJECT_GUIDE.md`
- `STATUS.md`

Disallowed files:

- unrelated Research workbench changes
- unrelated delivery-script work

## Deliverables

- Code changes:
  - deepen Support task input/output contracts and grounded result shape
  - improve the Support surface so the workflow is more than a thin launcher and result dump
- Docs changes:
  - capture the upgraded Support workflow shape in durable docs if the result contract changes

## Acceptance Criteria

- Support tasks remain runnable on the shared task runtime
- Support results are more structured and operator-readable than the current skeleton baseline
- the UI makes the Support case workflow feel intentionally grounded, not placeholder-level

## Verification Commands

- Backend:
  - `cd server`
  - `..\\.venv\\Scripts\\python.exe -m pytest tests/test_tasks.py tests/test_agent_service.py`
- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - a support workspace can launch and inspect the upgraded grounded case workflow
- Edge case:
  - limited support context still produces an honest degraded output instead of pretending grounding exists
- Error case:
  - invalid Support contract input fails cleanly without breaking the shared task runtime

## Risks

- overfitting Support too tightly to the Research result shape could erase real scenario differences

## Rollback Plan

- revert the Support workflow deepening while preserving the broader Stage C planning boundary