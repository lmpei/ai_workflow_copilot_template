# Task: AI Hot Tracker Content Pipeline Rebuild

## Goal

Rebuild `AI 热点追踪` around one real content chain: trusted external source intake, one structured middle layer, and one structured report-generation path.

## Project Phase

- Phase: Post-Stage-K bounded follow-through
- Scenario module: research

## Why

The current `AI 热点追踪` surface no longer needs a chat-first or MCP-first story. It needs one stable product path that can actually fetch current external information, normalize it into reusable tracking items, and generate a readable report instead of post-processing one large answer blob.

## Context

Relevant modules, dependencies, and related specs:

- `server/app/services/research_external_context_service.py`
- `server/app/services/ai_frontier_research_output_service.py`
- `server/app/services/ai_hot_tracker_follow_up_service.py`
- `server/app/services/model_interface_service.py`
- `server/app/services/ai_frontier_research_record_service.py`
- `server/app/schemas/ai_frontier_research.py`
- `web/components/research/ai-hot-tracker-workspace.tsx`

## Flow Alignment

- Flow A:
  - fetch latest items from one fixed trusted source set
- Flow B:
  - normalize source items into one bounded tracking schema
- Flow C:
  - generate one structured report from normalized items
- Flow D:
  - let the frontend consume that report directly and save it as one durable record when the user chooses
- Related APIs:
  - add one dedicated AI hot-tracker report endpoint instead of routing through the older generic chat path
- Related schema or storage changes:
  - extend `source_set_json` / record persistence to keep normalized source items and structured source metadata

## Dependencies

- Prior task:
  - `tasks/archive/stage-k/ai-hot-tracker-rename-and-surface-reframe.md`
- Blockers:
  - none inside the repo

## Scope

Allowed files:

- `server/app/api/routes/`
- `server/app/core/config.py`
- `server/app/schemas/`
- `server/app/services/`
- `server/app/repositories/`
- `server/app/models/` only if storage needs one bounded schema extension
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
  - one bounded external source intake layer
  - one structured normalized source-item layer
  - one structured report-generation service
  - one dedicated AI hot-tracker report API
  - one frontend integration that uses the new report path
- Test changes:
  - backend tests for source intake, normalization, and report generation
  - frontend verify pass
- Docs changes:
  - update control-plane docs to reflect the new active task and durable architecture changes

## Acceptance Criteria

- Works correctly
- Tests pass
- Lint passes
- Type checks pass
- Build impact is addressed
- `AI 热点追踪` no longer depends on the older generic chat answer blob for its primary report content

## Verification Commands

- Backend:
  - `cd server`
  - `..\\.venv\\Scripts\\python.exe -m pytest tests`
- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - external source intake returns normalized items and one structured report
- Edge case:
  - source intake succeeds but returns too few items, and report generation degrades clearly
- Error case:
  - source fetch fails and the report path returns one honest failure or degraded state

## Risks

- Remote source formats may vary across feeds and release pages
- A fixed source set can still be too thin if normalization rules are weak
- Structured output quality still depends on model behavior, so prompt and schema discipline must be tighter than the old answer-first path

## Rollback Plan

- Keep the older chat-based path intact while the new report endpoint is introduced
- Revert the frontend to the prior run path if the new endpoint proves unstable
