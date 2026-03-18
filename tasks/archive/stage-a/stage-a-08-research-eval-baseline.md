# Task: stage-a-08-research-eval-baseline

## Goal

Establish a repeatable Research evaluation baseline for structured results, formal reports, and trust signals so Stage
A changes can be checked for regression instead of relying on manual inspection alone.

## Project Stage

- Stage: Stage A
- Track: Platform Reliability

## Why

The Stage A trust baseline added runtime signals, but the project still needs a more explicit Research regression layer
to catch report-quality, grounding, and weak-evidence regressions as Research workflows deepen.

## Context

Relevant documents:

- `docs/prd/STAGE_A_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `docs/PROJECT_GUIDE.md`

Relevant runtime areas:

- `server/app/services/research_assistant_service.py`
- `server/app/services/chat_evaluator_service.py`
- `server/app/services/eval_execution_service.py`
- `server/app/services/task_execution_service.py`
- `server/tests/`

## Flow Alignment

- Flow A / B / C / D: Flow C / D with direct support for Flow B quality gates
- Related APIs: evals, tasks, research module outputs
- Related schema or storage changes: Research eval fixtures, expected report/trust checks, and regression coverage only as needed

## Dependencies

- Prior task: `tasks/stage-a-07-research-iteration-workflow.md`
- Blockers: none

## Scope

Allowed files:

- `server/app/services/`
- `server/app/schemas/`
- `server/tests/`
- `docs/PROJECT_GUIDE.md`

Disallowed files:

- unrelated frontend surfaces
- delivery or deployment docs unrelated to evaluation baselines

## Deliverables

- Code changes:
  - define a minimum Research regression baseline around structured results and formal report outputs
  - make trust and weak-evidence expectations explicit enough to check repeatedly
- Test changes:
  - add or update eval-oriented tests for grounded, weak-context, and failure-shaped Research outcomes
- Docs changes:
  - document the Research regression baseline and the intent of its checks

## Acceptance Criteria

- the repository has a repeatable Research regression baseline for Stage A result shapes
- weakly supported Research outcomes are flagged explicitly rather than treated as clean passes
- future Research changes can be checked against both report structure and trust expectations

## Verification Commands

- Backend:
  - `python -m compileall server/app server/tests`
  - `cd server`
  - `..\.venv\Scripts\python.exe -m pytest tests/test_research_assistant_service.py tests/test_chat_evaluator_service.py tests/test_eval_execution_service.py tests/test_task_execution_service.py`

## Tests

- Normal case:
  - a grounded Research output passes the baseline checks
- Edge case:
  - a documents-only or weak-context Research output produces explicit trust gaps instead of a silent pass
- Error case:
  - invalid or incomplete Research outputs fail baseline expectations clearly

## Risks

- making the baseline too brittle for the current Stage A scope instead of keeping it focused on the most meaningful trust checks

## Rollback Plan

- revert the Research eval-baseline changes while keeping the trust metadata and report flow already implemented

## Results

- added a stricter Stage A Research regression baseline for structured results, trust metadata, reports, and follow-up
  lineage
- wired regression baseline summaries into successful `research_task` traces so trust and regression outcomes remain
  inspectable together
- updated Research regression tests for grounded, weak-context, follow-up, and incomplete-result cases
- documented the distinction between the trust baseline and the stricter regression baseline in the project guide

## Execution Status

- Status: completed
- Completed At: 2026-03-18
- Notes: weak-context Research runs still return structured results, but they now fail the stricter regression baseline
  explicitly instead of being treated as clean passes

## Verification Result

- `python -m compileall server/app server/tests`
- `cd server`
- `..\.venv\Scripts\python.exe -m pytest tests/test_research_assistant_service.py tests/test_chat_evaluator_service.py tests/test_eval_execution_service.py tests/test_task_execution_service.py`
