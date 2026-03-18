# Task: stage-a-03-research-report-assembly-and-surface

## Goal

Build the first evidence-led Research report workflow and render it clearly in the frontend using the structured
contracts defined for Stage A.

## Project Stage

- Stage: Stage A
- Track: Research

## Why

Stage A should make `Research Assistant` feel like a real workflow, not just a task wrapper. That requires a stable
report assembly path and a frontend surface that can present structured research outputs clearly.

## Context

Relevant documents:

- `docs/prd/STAGE_A_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`

Relevant runtime areas:

- `server/app/services/research_assistant_service.py`
- `server/app/services/agent_service.py`
- `server/app/agents/`
- `server/tests/`
- `web/components/research/`
- `web/components/tasks/`
- `web/app/workspaces/[workspaceId]/tasks/`

## Flow Alignment

- Flow A / B / C / D: Flow B / C
- Related APIs: tasks, research module task execution, research results
- Related schema or storage changes: structured research report output only

## Dependencies

- Prior task: `tasks/archive/stage-a/stage-a-02-research-contracts-and-structured-results.md`
- Blockers: none

## Scope

Allowed files:

- `server/app/agents/`
- `server/app/services/`
- `server/app/schemas/`
- `server/tests/`
- `web/app/`
- `web/components/research/`
- `web/components/tasks/`
- `web/lib/`

Disallowed files:

- deployment files
- non-Research scenario surfaces unless shared task rendering must be adjusted

## Deliverables

- Code changes:
  - assemble a first formal Research report path with structured sections and evidence references
  - render the report cleanly in the Research/task UI
- Test changes:
  - add backend and frontend-adjacent coverage for report structure and evidence rendering assumptions
- Docs changes:
  - update docs only if the demo path or canonical report shape changes materially

## Acceptance Criteria

- the system can produce a structured Research report, not only a plain summary
- key findings remain connected to evidence
- the frontend can display structured Research output in a readable way
- the report path is stable enough for repeated demo use

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python.exe -m pytest tests`
- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - a formal Research report task produces all expected sections
- Edge case:
  - partial evidence still yields a coherent report with explicit gaps
- Error case:
  - report-generation failures remain observable and do not leave the task in an unclear state

## Risks

- a polished report surface can hide weak evidence handling if structure is added without strong source mapping

## Rollback Plan

- revert the formal Research report assembly path and UI updates while preserving the Stage A contracts

## Execution Status

- Status: planned
- Notes: this task deepens the Research workflow after the structured contracts are in place
