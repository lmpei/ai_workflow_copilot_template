# Task: phase3_docs_and_handoff

## Goal

Finalize Phase 3 documentation so the repository state, demo path, and remaining gaps are accurately recorded.

## Project Phase

- Phase: `Phase 3`
- Scenario module: `shared platform core`

## Why

Once tasks and agents are working, the docs must clearly describe what is real, what is still out of scope, and what the next phase will build on.

## Context

Relevant specs:

- `README.md`
- `AGENT_GUIDE.md`
- `docs/PROJECT_GUIDE.md`
- `docs/prd/PLATFORM_PRD.md`

Implementation defaults for this task:

- repository status should move to `Phase 3: Tasks + Agents`
- docs should present the minimal task-and-agent demo path
- docs must keep Phase 4 and Phase 5 work clearly out of scope

## Flow Alignment

- Flow C: task and agent execution demo path
- Related APIs:
  - task APIs
  - task/result frontend flow
- Related schema or storage changes:
  - none

## Dependencies

- Prior task:
  - all earlier Phase 3 tasks
- Blockers:
  - none

## Scope

Allowed files:

- `README.md`
- `AGENT_GUIDE.md`
- `docs/PROJECT_GUIDE.md`
- `docs/prd/PLATFORM_PRD.md`

Disallowed files:

- `server/`
- `web/`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`

## Deliverables

- Code changes:
  - none
- Test changes:
  - none unless a small verification note must be corrected
- Docs changes:
  - update current phase and demo path
  - record the implemented task-and-agent platform increment
  - keep future work explicitly out of scope

## Acceptance Criteria

- The docs consistently state that the repository is in `Phase 3: Tasks + Agents`
- The Phase 3 demo path is documented clearly
- Redis workers, LangGraph agent runs, and tool-call persistence are described as implemented
- Phase 4 observability depth and Phase 5 scenario modules remain clearly future work

## Verification Commands

- Backend:
  - use the verification results from prior Phase 3 tasks
- Frontend:
  - use the verification results from prior Phase 3 tasks

## Tests

- Normal case: documentation matches the implemented Phase 3 demo path
- Edge case: Phase 4 and Phase 5 boundaries remain explicit
- Error case: none

## Risks

- If docs imply scenario modules or advanced observability already exist, the repository state will become misleading again

## Rollback Plan

- revert documentation-only changes without affecting Phase 3 code
