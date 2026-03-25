# Task: stage-c-12-support-escalation-and-follow-up-workflow

## Goal

Deepen Support Copilot from a single-run grounded case task into a multi-step support workflow with follow-up lineage
and escalation packet output.

## Project Stage

- Stage: Stage C
- Track: Research-reference workflow depth applied to Support

## Why

`stage-c-02` gave Support a structured grounded case result, but support work still stops at one task output. Stage C
needs a clearer path from first-pass triage into follow-up handling and reviewer-facing escalation.

## Context

Relevant documents:

- `docs/prd/STAGE_C_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `docs/PROJECT_GUIDE.md`
- `tasks/archive/stage-c/stage-c-02-support-copilot-grounded-case-workflow.md`
- `tasks/archive/stage-c/stage-c-04-cross-module-quality-and-demo-readiness.md`

Relevant code surfaces:

- `server/app/schemas/support.py`
- `server/app/schemas/scenario.py`
- `server/app/services/support_copilot_service.py`
- `server/app/services/task_service.py`
- `web/components/support/`

## Flow Alignment

- Flow B / C: Support case execution and follow-up handling
- Related APIs: task creation, task inspection, scenario registry as needed
- Related schema or storage changes: task input/result contracts only unless follow-up validation requires minimal metadata wiring

## Dependencies

- Prior task: `tasks/archive/stage-c/stage-c-11-wave-two-planning.md`
- Blockers: none

## Scope

Allowed files:

- `server/app/schemas/support.py`
- `server/app/schemas/scenario.py`
- `server/app/services/support_copilot_service.py`
- `server/app/services/task_service.py`
- `server/app/services/agent_service.py` and `server/app/agents/graph.py` only if Support prompt/runtime changes are required
- `server/tests/`
- `web/components/support/`
- `web/lib/types.ts`
- `docs/PROJECT_GUIDE.md`
- `STATUS.md`
- `DECISIONS.md`

Disallowed files:

- unrelated module-name changes
- heavyweight Support-specific persistence layers unless the task cannot be solved through the shared task model

## Deliverables

- Code or contract changes:
  - add canonical Support follow-up input shape for continuing a prior case
  - add a reviewer-facing escalation packet result shape
  - make the Support panel support continuing a case and viewing the escalation packet
- Docs changes:
  - record the new Support workflow depth after completion

## Acceptance Criteria

- a collaborator can continue a Support case from a completed Support task without copying raw JSON by hand
- Support can produce an explicit escalation packet with evidence-linked findings, unresolved questions, and recommended owner signals
- limited-context Support runs still stay honest instead of pretending the escalation is grounded

## Verification Commands

- Backend:
  - `cd server`
  - `..\\.venv\\Scripts\\python.exe -m pytest tests`
- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - a grounded Support case can be continued into a follow-up or escalation run
- Edge case:
  - a limited-context Support case still produces an honest escalation packet with explicit gaps
- Error case:
  - invalid parent-task references or cross-module parent tasks are rejected cleanly

## Risks

- Support follow-up could accidentally reuse Research-only lineage assumptions if the Support contract is not explicit

## Rollback Plan

- revert the Support follow-up additions while preserving the Stage C planning boundary and prior grounded case workflow
