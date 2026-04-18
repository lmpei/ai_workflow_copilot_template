# AI Hot Tracker Record Write Contract

## Goal

Make the saved-record write path for `AI 热点追踪` produce correct persisted data by default, especially for empty
follow-up collections, instead of relying on response-time fallback behavior.

## Scope

- normalize `follow_ups` at write time for create and update
- keep the existing save and update API routes unchanged
- add test coverage that exercises the saved-record path with no follow-up entries

## Non-Goals

- redesign the report layout
- change the hot-tracker report-generation API
- introduce database backfills for older saved records

## Verification

- `cd server`
- `..\\.venv\\Scripts\\python.exe -m pytest tests`
- `git diff --check`
