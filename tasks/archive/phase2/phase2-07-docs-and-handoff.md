# Task: phase2_docs_and_handoff

## Goal

Update project docs and handoff notes so the repository status, demo path, and known limits accurately reflect completed Phase 2 behavior.

## Project Phase

- Phase: `Phase 2`
- Scenario module: `shared platform core`

## Why

Phase 2 adds real ingest and grounded retrieval. If the docs are not updated, the repo will still read like a Phase 1 MVP and confuse the next implementation phase.

## Context

Relevant specs:

- `README.md`
- `docs/prd/PLATFORM_PRD.md`
- `docs/PROJECT_GUIDE.md`
- `AGENT_GUIDE.md`

Current state:

- docs currently describe the repo as `Phase 1: Platform MVP`
- the current docs explicitly say real RAG is not implemented yet

Implementation defaults for this task:

- update only status, capabilities, demo path, and remaining-scope language
- do not present Redis workers, LangGraph agents, or eval pipelines as complete

## Flow Alignment

- Flow A / Flow B completed Phase 2 handoff
- Related APIs:
  - `documents`
  - `chat`
  - `metrics` where wording depends on real trace behavior
- Related schema or storage changes:
  - none directly; documentation only

## Dependencies

- Prior task:
  - all earlier Phase 2 tasks
- Blockers: none

## Scope

Allowed files:

- `README.md`
- `AGENT_GUIDE.md`
- `docs/PROJECT_GUIDE.md`
- `docs/prd/PLATFORM_PRD.md`

Disallowed files:

- `server/app/workers/`
- `server/app/agents/`
- `web/`

## Deliverables

- Code changes:
  - none expected except incidental test/docs cleanup if required
- Test changes:
  - add or adjust verification notes only if the Phase 2 run path changed
- Docs changes:
  - mark the repo as `Phase 2`
  - describe the new ingest + RAG demo path
  - list the remaining Phase 3+ gaps clearly

## Acceptance Criteria

- Docs accurately describe the implemented Phase 2 capabilities
- Docs still clearly state that tasks, agents, and evaluation are not complete yet
- Handoff notes give the next phase a clean input state

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python -m ruff check .`
  - `..\.venv\Scripts\python -m mypy app`
  - `..\.venv\Scripts\python -m pytest`
- Frontend:
  - `cd web`
  - `npm.cmd run verify`

## Tests

- Normal case: docs match the actual demo flow and repo state
- Edge case: limitations for unfinished Phase 3+ work are still explicit
- Error case: none

## Risks

- If docs overstate completion here, Phase 3 planning will start from false assumptions

## Rollback Plan

- revert the documentation changes and preserve the previously committed Phase 1 doc set
