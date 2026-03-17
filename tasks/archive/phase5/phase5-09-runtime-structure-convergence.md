# Task: phase5-09-runtime-structure-convergence

## Goal

Converge runtime code structure, workspace module naming, and heavy service boundaries without changing product behavior.

## Project Phase

- Phase: Phase 5
- Scenario module: shared platform core plus scenario modules

## Why

Phase 5 now has enough real runtime behavior that leftover placeholder files, duplicate workspace module fields, and
inconsistent frontend container names are increasing the cost of change. This task tightens those seams before later
module expansion adds more weight.

## Context

This is a structure-convergence task, not a feature-delivery task. It should leave the existing platform behavior and
the current module product names intact while making runtime paths, module contracts, and service boundaries easier to
understand and extend.

## Flow Alignment

- Flow A / B / C / D: Flow A / B / C / D
- Related APIs: workspace, documents, chat, tasks, evals, analytics
- Related schema or storage changes: workspace request/response contract normalization only; no database column removal

## Dependencies

- Prior task: phase5-08-docs-and-handoff
- Blockers: none

## Scope

Allowed files:

- `server/app/`
- `server/tests/`
- `web/app/`
- `web/components/`
- `web/lib/`
- `docs/PROJECT_GUIDE.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/prd/PLATFORM_PRD.md`

Disallowed files:

- `docs/prd/PRD_TEMPLATE.md`
- `docs/architecture/ARCHITECTURE_TEMPLATE.md`
- `.github/`
- `docker-compose.yml`

## Deliverables

- Code changes:
  - Remove placeholder worker entrypoints that do not participate in runtime execution
  - Make `module_type` the canonical workspace module concept and keep `type` as a compatibility alias
  - Normalize frontend container naming to a stable `Manager` / `Panel` / `Placeholder` scheme
  - Extract first-layer helper modules from the heaviest backend services while preserving current facades
- Test changes:
  - Update workspace, task, eval, chat, and document tests to follow the canonical `module_type` path
  - Add compatibility coverage so legacy `type` payloads still work during the transition window
- Docs changes:
  - Record the runtime structure convergence task as the source-of-truth execution note
  - Clarify frontend naming rules and worker-directory intent
  - Document the distinct responsibilities of the research, support, and job modules without renaming them

## Acceptance Criteria

- `module_type` is the only authoritative workspace module concept in runtime code
- `server/app/workers/` only contains real async job entrypoints
- Frontend container naming is stable and predictable
- Module boundary docs directly explain the difference between research, support, and job
- `document_service.py`, `eval_execution_service.py`, and `retrieval_service.py` each delegate at least one internal
  responsibility to a dedicated helper module
- Existing API routes, worker job names, and product behavior remain intact

## Verification Commands

- Backend:
  - `python -m compileall server/app server/tests`
  - `pytest server/tests`
- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case: workspace CRUD, document ingest, chat, tasks, evals, and analytics still work after structure changes
- Edge case: legacy workspace payloads that only send `type` still normalize to `module_type`
- Error case: restructured services continue to preserve existing error handling and failure states

## Risks

- Broad renames can leave stale imports if runtime pages and components are not updated together
- Workspace field normalization can silently drift if compatibility coverage is incomplete
- Service extraction can regress error handling if facade entrypoints do not keep ownership of lifecycle transitions

## Rollback Plan

- Revert the PR stack in reverse order if a later extraction introduces instability
- Preserve the current `type` column throughout this task so rollback does not require a schema migration
- Keep route-level and worker-level public entrypoints stable so rollback stays file-local

## Final Results

- Placeholder worker files were removed so `server/app/workers/` only describes live async entrypoints.
- Workspace runtime flows now normalize to `module_type`, while `type` remains a compatibility alias at the schema boundary.
- Frontend container names now follow the `Manager` / `Panel` / `Placeholder` convention.
- Research, support, and job module boundaries were centralized in docs and shared metadata.
- `document_service.py`, `eval_execution_service.py`, and `retrieval_service.py` now delegate internal responsibilities to dedicated helper modules.

## Execution Status

- Status: completed
- Completed on: 2026-03-17
- Verification:
  - `python -m compileall server/app server/tests` -> passed
  - `..\\.venv\\Scripts\\python.exe -m pytest tests` (run from `server/`) -> 118 passed
  - `npm --prefix web run verify` -> passed
- Notes: task document updated with final results and ready for archival under `tasks/archive/phase5/`.
