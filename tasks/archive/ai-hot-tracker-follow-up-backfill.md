# AI Hot Tracker Follow-Up Backfill

## Goal

Backfill older `AI 热点追踪` saved records so the persisted `follow_ups` field is always present as a list, then stop
relying on response-time fallback for this historical inconsistency.

## Scope

- add one bounded migration that normalizes missing or invalid `follow_ups` values to `[]`
- ensure new saved-record writes always persist `follow_ups` as a list at the source path
- keep the read contract strict so bad persisted data is not silently masked

## Non-Goals

- redesign the hot-tracker page
- change the save or update API route shape
- alter unrelated `source_set` keys

## Verification

- `cd server`
- `..\\.venv\\Scripts\\python.exe -m pytest tests`
- `git diff --check`
