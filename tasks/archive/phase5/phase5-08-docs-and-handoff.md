# Task: phase5-08-docs-and-handoff

## Goal

Update project docs so repository status, demo path, and remaining scope all reflect completed Phase 5 work.

## Project Phase

- Phase: Phase 5
- Scenario module: shared platform core plus scenario modules

## Why

Phase 5 changes the story from platform-only primitives to reusable scenario-module product flows. The docs must match that reality.

## Context

The docs of record should move from Phase 4 to Phase 5 only after at least one strong module MVP and the supporting skeletons are real.

## Flow Alignment

- Flow A / B / C / D: Flow B / C / D
- Related APIs: scenario module APIs, evals, analytics
- Related schema or storage changes: none required

## Dependencies

- Prior task: all previous Phase 5 tasks
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
  - Update current phase and demo path to Phase 5
  - Record implemented scenario-module capabilities
  - Keep post-Phase-5 expansion clearly out of scope

## Acceptance Criteria

- Docs consistently identify the repository as `Phase 5: Scenario Modules`
- Demo path reflects at least one real scenario-module MVP and the lighter module skeletons
- Remaining scope stays limited to later expansion work

## Verification Commands

- Backend:
  - Reference the final Phase 5 backend verification baseline
- Frontend:
  - Reference the final Phase 5 frontend verification baseline

## Tests

- Normal case: docs match the implemented feature set
- Edge case: deeper future scenario work is not presented as complete
- Error case: none

## Risks

- Handoff docs can drift if they are updated before the scenario-module implementations are actually stable

## Rollback Plan

- Revert the doc-only handoff changes if implementation status changes
