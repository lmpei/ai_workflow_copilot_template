# Task: phase4-05-chat-evaluator-framework

## Goal

Implement the first evaluator framework for retrieval-backed chat using a mix of rule-based checks and LLM-as-judge scoring.

## Project Phase

- Phase: Phase 4
- Scenario module: shared platform core

## Why

Phase 4 should measure quality, not just latency and token counts. Retrieval-backed chat is the most mature first target.

## Context

The current platform already supports grounded chat with citations, traces, and live provider configuration. This task should evaluate those existing outputs without expanding into scenario-specific logic.

## Flow Alignment

- Flow A / B / C / D: Flow D, evaluating Flow B
- Related APIs: eval run execution from `phase4-04`
- Related schema or storage changes: `eval_results`, traces

## Dependencies

- Prior task: `phase4-04-eval-runner-and-worker-execution`
- Blockers: none

## Scope

Allowed files:

- `server/app/core/`
- `server/app/services/`
- `server/app/repositories/`
- `server/tests/`
- `.env.example`

Disallowed files:

- `web/`
- `server/app/agents/`
- `server/app/api/routes/tasks.py`

## Deliverables

- Code changes:
  - Add evaluator framework for retrieval-backed chat
  - Implement rule-based checks such as answer presence, source presence, and expected document hit
  - Implement LLM judge path behind separate eval configuration
- Test changes:
  - Add evaluator tests for rule checks and mocked judge scoring
- Docs changes:
  - None required in this task

## Acceptance Criteria

- Eval results can contain rule-based scores and judge-based scores together
- Judge model/provider config is separate from primary chat config
- Retrieval-backed chat is the only required eval target in this phase
- Tests pass
- Lint passes
- Type checks pass

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python -m ruff check .`
  - `..\.venv\Scripts\python -m mypy app`
  - `..\.venv\Scripts\python -m pytest`
- Frontend:
  - None

## Tests

- Normal case: evaluator scores a successful grounded answer
- Edge case: answer exists but sources are missing and the rule score reflects that
- Error case: judge provider failure is captured without losing the eval result record

## Risks

- Over-reliance on LLM judging could make scores unstable if rules are not kept alongside it

## Rollback Plan

- Revert evaluator logic while preserving the eval dataset/run infrastructure
