# Task: stage-b-06-research-briefs-and-asset-comparison

## Goal

Turn the Stage B Research workbench into a more reusable workflow by introducing explicit Research briefs and
comparison across assets or revisions.

## Project Stage

- Stage: Stage B
- Track: Research

## Why

Stage B wave one made Research work persistent through assets and revisions, but the workbench still lacks a clear
brief layer and a direct way to compare related Research runs over time. The next Research wave should make those
workflow assets easier to reopen, branch, and inspect.

## Context

Relevant documents:

- `docs/prd/STAGE_B_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `docs/PROJECT_GUIDE.md`

Relevant runtime areas:

- `server/app/schemas/`
- `server/app/repositories/`
- `server/app/services/`
- `server/app/api/routes/`
- `server/tests/`
- `web/lib/`
- `web/components/research/`

## Flow Alignment

- Flow A / B / C / D: Flow B / C / D
- Related APIs: Research asset endpoints and Research task creation paths
- Related schema or storage changes: Research asset and revision contracts as needed

## Dependencies

- Prior task: `tasks/archive/stage-b/stage-b-05-wave-two-planning.md`
- Blockers: none

## Scope

Allowed files:

- `server/app/schemas/`
- `server/app/repositories/`
- `server/app/services/`
- `server/app/api/routes/`
- `server/tests/`
- `web/lib/`
- `web/components/research/`
- `docs/PROJECT_GUIDE.md`

Disallowed files:

- support or job module productization
- unrelated delivery automation or runtime recovery changes

## Deliverables

- Code changes:
  - define a reusable Research brief shape derived from saved assets or revisions
  - expose a comparison path for related Research assets or revisions
  - surface the workflow clearly in the Research workbench
- Test changes:
  - add or update coverage for Research brief persistence and comparison behavior
- Docs changes:
  - update the developer-facing Research lifecycle docs if the canonical asset workflow changes

## Acceptance Criteria

- a saved Research asset exposes a stable brief-like summary of its intent and current state
- a collaborator can compare two related Research assets or revisions without manually inspecting raw JSON
- Research workbench behavior remains consistent with Stage B asset and lineage expectations

## Verification Commands

- Backend:
  - `python -m compileall server/app server/tests`
  - `cd server`
  - `..\.venv\Scripts\python.exe -m pytest tests/test_research_assets.py tests/test_tasks.py tests/test_research_assistant_service.py`
- Frontend:
  - `cmd /c npm --prefix web run verify`

## Tests

- Normal case:
  - a saved Research asset exposes a reusable brief and can be compared with another asset or revision
- Edge case:
  - comparison still works when assets share some but not all focus areas or open questions
- Error case:
  - invalid or cross-asset revision references are rejected clearly

## Risks

- over-designing the brief layer too early could lock the workbench into a shape that later Research productization may outgrow

## Rollback Plan

- revert the Research brief and comparison changes while preserving the Stage B asset lifecycle and follow-up flow
