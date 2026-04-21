# Task: AI Hot Tracker Ranking and Delta Decision Layer

## Goal

Deepen `AI 热点追踪` from a durable tracking loop into a more selective agent by adding ranking, novelty, clustering, and stronger change-detection logic ahead of report synthesis.

## Project Phase

- Phase: Post-Stage-K bounded follow-through
- Scenario module: research

## Why

The current hot-tracker foundation can fetch trusted sources, persist runs, generate structured reports, and support grounded follow-up. What it still lacks is a real decision layer. Without ranking and temporal grouping, it behaves too much like a time-ordered summarizer instead of an agent that decides what is actually worth surfacing.

## Context

Relevant modules, dependencies, and related specs:

- `server/app/services/ai_hot_tracker_source_service.py`
- `server/app/services/ai_hot_tracker_report_service.py`
- `server/app/services/ai_hot_tracker_tracking_service.py`
- `server/app/repositories/ai_hot_tracker_tracking_run_repository.py`
- `server/app/schemas/ai_frontier_research.py`
- `server/tests/test_ai_hot_tracker_source_service.py`
- `server/tests/test_ai_hot_tracker_tracking_runs.py`
- `web/components/research/ai-hot-tracker-workspace.tsx`

## Flow Alignment

- Flow A:
  - source intake continues to fetch from the fixed trusted source families
- Flow B:
  - normalized source items gain a bounded scoring layer across freshness, source authority, novelty, and workspace relevance
- Flow C:
  - overlapping items are grouped into event-level clusters before report synthesis
- Flow D:
  - run-to-run delta compares grouped events, not only raw URLs
- Flow E:
  - the report and notify decision reflect ranked and grouped results instead of raw intake order

## Dependencies

- Prior task:
  - `tasks/archive/ai-hot-tracker-tracking-agent-foundation.md`
- Blockers:
  - none inside the repo

## Scope

Allowed files:

- `server/app/schemas/`
- `server/app/services/`
- `server/app/repositories/`
- `server/tests/`
- `web/components/research/`
- `web/lib/`
- control-plane docs

Disallowed files:

- deployment and environment files
- module product names
- unrelated support/job workflow files

## Deliverables

- Code changes:
  - bounded source-item scoring for freshness, authority, novelty, and relevance
  - bounded clustering or grouping of overlapping source items into event-level units
  - stronger delta detection between the latest run and the previous run
  - clearer `should_notify` and priority signals exposed to the frontend
- Test changes:
  - backend tests for ranking order, clustering behavior, and delta-state transitions
  - frontend verify pass
- Docs changes:
  - update control-plane docs to reflect the stronger decision layer

## Acceptance Criteria

- Works correctly
- Tests pass
- Lint passes
- Type checks pass
- Build impact is addressed
- the hot tracker no longer treats raw item order as the primary decision layer
- run-to-run change state reflects grouped changes rather than only raw URL differences

## Verification Commands

- Backend:
  - `cd server`
  - `..\\.venv\\Scripts\\python.exe -m pytest tests`
- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - new relevant items outrank older or lower-authority items
- Edge case:
  - multiple sources covering the same event are grouped instead of duplicated across the brief
- Error case:
  - partial source failure still produces ranked output and an honest delta summary

## Risks

- authority scoring can become hand-wavy if it is not fixed and inspectable
- clustering can over-merge distinct items if rules are too loose
- novelty scoring can oscillate if it depends too heavily on unstable titles instead of stronger identifiers

## Rollback Plan

- keep the current tracking-run persistence and report-generation flow intact
- revert only the ranking and grouping layer if the new decision logic proves too noisy
