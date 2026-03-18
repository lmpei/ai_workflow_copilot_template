# Task: stage-a-02-research-contracts-and-structured-results

## Goal

Introduce the canonical Stage A Research task contract and a structured Research result schema that can support deeper
report workflows without breaking the existing shared platform primitives.

## Project Stage

- Stage: Stage A
- Track: Research

## Why

Research cannot become a reusable workflow while its inputs and outputs remain too loose. Stage A needs a stable
contract for research intent, scope, and result structure before report assembly and iteration can deepen.

## Context

Relevant documents:

- `docs/prd/STAGE_A_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`

Relevant runtime areas:

- `server/app/schemas/`
- `server/app/services/research_assistant_service.py`
- `server/app/services/task_service.py`
- `server/app/services/task_execution_service.py`
- `web/lib/types.ts`
- `web/components/research/`

## Flow Alignment

- Flow A / B / C / D: Flow B / C / D
- Related APIs: tasks, workspaces, research module surfaces
- Related schema or storage changes: research task input contract and research result contract

## Dependencies

- Prior task: `tasks/archive/stage-a/stage-a-01-task-stack-planning.md`
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

- deployment files
- unrelated scenario-module surfaces

## Deliverables

- Code changes:
  - define a structured Research task input contract
  - define a canonical structured Research result contract
  - keep shared task primitives intact while upgrading the Research-specific layer
- Test changes:
  - add or update tests for valid structured inputs and outputs
  - preserve compatibility where current Research task entry points must continue to work
- Docs changes:
  - update project guide only if the canonical Research contract shape changes developer expectations

## Acceptance Criteria

- Research tasks can carry structured intent, scope, and output expectations
- Research results have a stable shape that supports summary, findings, evidence, and next-step sections
- Shared platform task primitives remain the source of truth
- Existing Research entry points still behave predictably

## Verification Commands

- Backend:
  - `python -m compileall server/app server/tests`
  - `cd server`
  - `..\.venv\Scripts\python.exe -m pytest tests/test_research_assistant_service.py tests/test_tasks.py tests/test_agent_service.py tests/test_task_execution_service.py`
- Frontend:
  - `cmd /c npm --prefix web run verify`

## Tests

- Normal case:
  - a Research task can be created with a structured input payload and returns a structured result
- Edge case:
  - optional research fields can be omitted while defaults remain valid
- Error case:
  - invalid Research contract shapes are rejected clearly

## Risks

- over-specializing the shared task model instead of keeping the Research contract scoped to the module layer

## Rollback Plan

- revert the Research-specific schema and service changes while keeping the Stage A task files and planning docs intact

## Results

- added a canonical Research module-layer input contract with:
  - `goal`
  - `focus_areas`
  - `key_questions`
  - `constraints`
  - `deliverable`
  - `requested_sections`
- added a canonical structured Research result shape with normalized `input` and structured `sections`
- kept shared task primitives generic while resolving the richer Research contract inside the Research module layer
- updated the Research task surface to launch structured task payloads and render structured results
- added backend regression coverage for normalization, structured task creation, agent execution, and task execution
- updated `docs/PROJECT_GUIDE.md` to document the new Stage A Research contract expectations

## Execution Status

- Status: completed
- Completed At: 2026-03-18
- Notes: Stage A Research contracts and structured results are now implemented and verified; the next active task is `stage-a-03`
