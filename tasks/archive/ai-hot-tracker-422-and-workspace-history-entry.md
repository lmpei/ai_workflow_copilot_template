# Task: AI Hot Tracker 422 And Workspace History Entry

## Goal

Fix the `AI 热点追踪` saved-records 422 error and restore one lightweight, real entry for viewing system-level workspace history.

## Project Phase

- Phase: Post-Stage-K follow-up
- Scenario module: research plus shared workspace navigation

## Why

The current `AI 热点追踪` page fails on load because it requests too many saved records, and the homepage still links to `/workspaces` even though that route only redirects back home. We need one direct fix for the broken report page and one light system-level history surface so users can actually find prior workspaces again.

## Context

Relevant modules, dependencies, and related specs:

- `web/components/research/ai-hot-tracker-workspace.tsx`
- `web/app/workspaces/page.tsx`
- `web/lib/api.ts`
- `server/app/api/routes/research_analysis_runs.py`

## Flow Alignment

- Flow A:
  - load saved AI report records without violating backend query constraints
- Flow B:
  - open one lightweight workspace-history page from the existing `/workspaces` entry
- Related APIs:
  - `GET /workspaces/{workspace_id}/ai-frontier-records`
  - `GET /workspaces`
- Related schema or storage changes:
  - none

## Dependencies

- Prior task:
  - `tasks/ai-hot-tracker-content-pipeline-rebuild.md`
- Blockers:
  - none inside the repo

## Scope

Allowed files:

- `web/components/research/`
- `web/components/workspace/`
- `web/app/workspaces/`
- `web/lib/`
- control-plane docs

Disallowed files:

- deployment and environment files
- unrelated support/job workflow files
- destructive workspace data deletion without a bounded follow-up task

## Deliverables

- Code changes:
  - fix the saved-records query limit mismatch in `AI 热点追踪`
  - replace the `/workspaces` redirect with one lightweight workspace-history page
- Test changes:
  - frontend verify pass
- Docs changes:
  - update control-plane docs so the live active task reflects the fix

## Acceptance Criteria

- `AI 热点追踪` no longer throws `422 Unprocessable Entity` during saved-record load
- `/workspaces` shows one lightweight list of the user’s workspaces
- existing homepage “查看全部工作区” link now lands on a real page
- frontend verification passes

## Verification Commands

- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - signed-in user opens `AI 热点追踪` and saved records load without 422
- Edge case:
  - signed-in user with zero workspaces sees an empty-state message on `/workspaces`
- Error case:
  - signed-in user with API failure sees one readable error state on `/workspaces`

## Risks

- the repo still lacks a bounded system-level workspace delete path, so this task should restore visibility first rather than overreach into destructive behavior

## Rollback Plan

- revert the `/workspaces` page to the prior redirect
- revert the saved-record limit change in `AI 热点追踪`
