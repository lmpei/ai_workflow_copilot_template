# Task: AI Hot Tracker Product Closure

## Goal

Close `AI 热点追踪` as a real workspace-scoped product by replacing the research-style report contract with a brief contract, exposing runtime state, adding an internal evaluation view, and tightening the report plus follow-up surface into one product-grade brief workflow.

## Project Phase

- Phase: Post-Stage-K bounded follow-through
- Scenario module: research

## Why

The hot-tracker loop now has real source intake, ranking, clustering, delta detection, persistence, and scheduled evaluation, but it still leaks research-era output structure, garbled copy, and incomplete product state visibility. The next bounded task is to close the gap between “working pipeline” and “real product.”

## Context

Relevant modules, dependencies, and related specs:

- `server/app/schemas/ai_frontier_research.py`
- `server/app/services/ai_hot_tracker_report_service.py`
- `server/app/services/ai_hot_tracker_follow_up_service.py`
- `server/app/services/ai_hot_tracker_tracking_service.py`
- `server/app/api/routes/research_analysis_runs.py`
- `web/components/research/ai-hot-tracker-workspace.tsx`
- `web/lib/types.ts`
- `web/lib/api.ts`

## Flow Alignment

- Flow A:
  - trusted source intake, ranking, clustering, and delta remain the backend truth
- Flow B:
  - synthesis now produces a brief-oriented contract instead of a research-oriented contract
- Flow C:
  - run state and next scheduled evaluation become visible to the workspace UI
- Flow D:
  - follow-up continues to ground strictly on the selected run and its sources
- Flow E:
  - an internal evaluation view exposes ranked items, clusters, and delta reasoning without entering the consumer-facing product path

## Dependencies

- Prior task:
  - `tasks/archive/ai-hot-tracker-ranking-and-delta-decision-layer.md`
- Blockers:
  - none inside the repo

## Scope

Allowed files:

- `server/app/schemas/`
- `server/app/services/`
- `server/app/repositories/`
- `server/app/api/routes/`
- `server/tests/`
- `web/components/research/`
- `web/lib/`
- control-plane docs

Disallowed files:

- deployment and environment files
- module product names
- unrelated support or job workflow files

## Deliverables

- Code changes:
  - new hot-tracker brief output contract
  - workspace state endpoint for runtime visibility
  - internal run evaluation endpoint
  - productized brief + follow-up UI
  - hot-tracker copy cleanup
- Test changes:
  - backend coverage for brief output, state endpoint, and evaluation endpoint
  - frontend verify pass
- Docs changes:
  - update control-plane docs to reflect product closure and archive the completed task

## Acceptance Criteria

- Works correctly
- Tests pass
- Lint passes
- Type checks pass
- Build impact is addressed
- `AI 热点追踪` no longer renders the old research-style output contract
- the workspace can show recent check state even when no new scheduled run was saved
- the internal evaluation view exposes ranked items, clustered signals, and delta reasoning
- hot-tracker surfaces show normal Chinese copy instead of garbled text

## Verification Commands

- Backend:
  - `cd server`
  - `..\\.venv\\Scripts\\python.exe -m pytest tests`
- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - manual run creates a saved brief and renders the selected run as a brief
- Edge case:
  - steady-state scheduled evaluation updates tracking state without creating a new saved run
- Error case:
  - degraded or failed runs expose honest state and error information without fallback garbage copy

## Risks

- changing the hot-tracker output contract can accidentally break older research-oriented consumers
- the evaluation view can drift into a public debug UI if it is not clearly isolated
- copy cleanup can miss deeply embedded defaults if prompt strings and schema defaults are not updated together

## Rollback Plan

- keep ranking, clustering, delta, and tracking-state persistence intact
- revert only the new brief contract and UI surface if the product closure change proves unstable
