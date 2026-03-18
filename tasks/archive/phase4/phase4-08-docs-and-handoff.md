# Task: phase4-08-docs-and-handoff

## Goal

Update project docs so repository status, demo path, and remaining scope all reflect completed Phase 4 work.

## Project Phase

- Phase: Phase 4
- Scenario module: shared platform core

## Why

Phase 4 changes the platform story from basic task execution to measured quality and observability. The handoff docs must match that reality.

## Context

The docs of record should move from Phase 3 to Phase 4 only after eval and observability surfaces are real.

## Flow Alignment

- Flow A / B / C / D: Flow D
- Related APIs: evals, metrics, analytics
- Related schema or storage changes: none required

## Dependencies

- Prior task: all previous Phase 4 tasks
- Blockers: none

## Scope

Allowed files:

- `README.md`
- `AGENT_GUIDE.md`
- `docs/PROJECT_GUIDE.md`
- `docs/prd/PLATFORM_PRD.md`

Disallowed files:

- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `server/`
- `web/`

## Deliverables

- Code changes:
  - None
- Test changes:
  - None unless a missing verification note must be corrected
- Docs changes:
  - Update current phase and demo path to Phase 4
  - Record implemented eval/observability capabilities
  - Keep Phase 5 scenario work clearly out of scope

## Acceptance Criteria

- Docs consistently identify the repository as `Phase 4: Evaluation + Observability`
- Demo path reflects eval run creation, execution, and review
- Remaining scope stays limited to later-phase work

## Verification Commands

- Backend:
  - Reference the final Phase 4 backend verification baseline
- Frontend:
  - Reference the final Phase 4 frontend verification baseline

## Tests

- Normal case: docs match the implemented feature set
- Edge case: partial or future-only Phase 5 work is not presented as complete
- Error case: none

## Risks

- Handoff docs can drift if they are updated before implementation is actually stable

## Rollback Plan

- Revert the doc-only handoff changes if implementation status changes
