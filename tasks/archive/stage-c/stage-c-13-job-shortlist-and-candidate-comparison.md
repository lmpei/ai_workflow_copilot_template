# Task: stage-c-13-job-shortlist-and-candidate-comparison

## Goal

Deepen Job Assistant from single candidate or JD reviews into a shortlist and candidate-comparison workflow.

## Project Stage

- Stage: Stage C
- Track: Research-reference workflow depth applied to Job

## Why

`stage-c-03` gave Job a structured hiring-review result, but hiring work still ends at one task output. Stage C needs a
clearer path from individual grounded reviews into comparative shortlist decisions.

## Context

Relevant documents:

- `docs/prd/STAGE_C_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `docs/PROJECT_GUIDE.md`
- `tasks/archive/stage-c/stage-c-03-job-assistant-structured-hiring-workflow.md`
- `tasks/archive/stage-c/stage-c-04-cross-module-quality-and-demo-readiness.md`

Relevant code surfaces:

- `server/app/schemas/job.py`
- `server/app/schemas/scenario.py`
- `server/app/services/job_assistant_service.py`
- `server/app/services/task_service.py`
- `web/components/job/`

## Flow Alignment

- Flow B / C: Job review execution and candidate comparison handling
- Related APIs: task creation, task inspection, scenario registry as needed
- Related schema or storage changes: task input/result contracts only unless comparison validation requires minimal metadata wiring

## Dependencies

- Prior task: `tasks/archive/stage-c/stage-c-11-wave-two-planning.md`
- Blockers: none

## Scope

Allowed files:

- `server/app/schemas/job.py`
- `server/app/schemas/scenario.py`
- `server/app/services/job_assistant_service.py`
- `server/app/services/task_service.py`
- `server/app/services/agent_service.py` and `server/app/agents/graph.py` only if Job prompt/runtime changes are required
- `server/tests/`
- `web/components/job/`
- `web/lib/types.ts`
- `docs/PROJECT_GUIDE.md`
- `STATUS.md`
- `DECISIONS.md`

Disallowed files:

- unrelated module-name changes
- heavyweight Job-specific persistence layers unless the task cannot be solved through the shared task model

## Deliverables

- Code or contract changes:
  - add canonical Job comparison input shape for selecting grounded candidate-review tasks
  - add shortlist and candidate-comparison result fields
  - make the Job panel support selecting candidate reviews and inspecting shortlist output
- Docs changes:
  - record the new Job workflow depth after completion

## Acceptance Criteria

- a collaborator can compare multiple grounded Job review tasks for the same role without manually diffing raw JSON
- Job can produce a shortlist-style output with evidence-linked findings, risks, and interview focus
- missing evidence or thin grounding remains explicit instead of implying a final hiring decision

## Verification Commands

- Backend:
  - `cd server`
  - `..\\.venv\\Scripts\\python.exe -m pytest tests`
- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - multiple Job review tasks can feed a candidate-comparison or shortlist run
- Edge case:
  - thin-context candidate comparisons still surface gaps and avoid overconfident ranking
- Error case:
  - invalid comparison task references or cross-module task references are rejected cleanly

## Risks

- Job comparison could overstate decision certainty if the new result contract does not preserve reviewer-facing caution

## Rollback Plan

- revert the Job shortlist additions while preserving the Stage C planning boundary and prior structured hiring workflow
