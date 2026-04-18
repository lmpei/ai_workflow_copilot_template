# Task

- ID: TEMP-2026-04-17-WORKSPACE-DELETE-VIEWPORT
- Title: fix workspace delete success feedback and remove initial AI hot tracker page scrollbar
- Status: completed

## Goal

Fix two bounded regressions:

1. deleting a workspace from `/workspaces` should not show a false failure after the backend already succeeded
2. entering `AI 热点追踪` should not immediately produce a browser-page scrollbar

## Scope

- make successful no-content API responses parse correctly in the shared frontend client
- keep workspace delete UI on the same success path and let local state update without a spurious error
- tighten the `AI 热点追踪` page shell so the browser page fits inside one viewport on first load
- move overflow into module-owned panes instead of the browser body

## Out of Scope

- redesign the `/workspaces` page
- change workspace delete semantics
- redesign the `AI 热点追踪` report content itself

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests`
- `npm --prefix web run verify`
- `git diff --check`
