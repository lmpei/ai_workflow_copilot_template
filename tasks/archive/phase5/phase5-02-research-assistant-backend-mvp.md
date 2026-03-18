# Task: phase5-02-research-assistant-backend-mvp

## Goal

Implement the first full scenario-module backend MVP using Research Assistant flows on top of the existing platform core.

## Project Phase

- Phase: Phase 5
- Scenario module: research

## Why

Research Assistant is the closest fit to the current RAG, task, and agent capabilities, so it should become the first end-to-end scenario module proving the platform design.

## Context

This task should reuse workspaces, documents, retrieval-backed chat, tasks, LangGraph runtime, and eval primitives instead of creating a separate subsystem.

## Flow Alignment

- Flow A / B / C / D: Flow B / C / D
- Related APIs: documents, chat, tasks, evals
- Related schema or storage changes: research-specific task inputs and outputs

## Dependencies

- Prior task:
  - `phase5-01-module-configuration-and-scenario-contracts`
- Blockers: none

## Scope

Allowed files:

- `server/app/api/routes/`
- `server/app/services/`
- `server/app/agents/`
- `server/app/schemas/`
- `server/app/repositories/`
- `server/tests/`

Disallowed files:

- `server/app/workers/`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`

## Deliverables

- Code changes:
  - Add Research Assistant task/agent flow for summary/report style outputs
  - Add research-specific structured result contract
- Test changes:
  - Add API/service tests for research task execution
- Docs changes:
  - None required in this task

## Acceptance Criteria

- Research Assistant can create and execute a research-focused task flow
- Result payload is structured and reusable
- Existing task/agent primitives are reused
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
  - None required in this task

## Tests

- Normal case: research summary task completes with structured output
- Edge case: sparse document context still returns a bounded result shape
- Error case: invalid module/task combination is rejected

## Risks

- Turning research flows into ad-hoc prompts would weaken the scenario contract

## Rollback Plan

- Revert research-specific services and schemas while preserving the shared platform task runtime
