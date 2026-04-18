# Status

Current state only. Keep this file short, current, and action-oriented.

## Metadata

- Last Updated: 2026-04-17

## Project Mode

- Execution

## Current Phase

- Phase 5 baseline complete
- Stage A complete and closed
- Stage B complete and closed
- Stage C complete and closed
- Stage D complete and closed
- Stage E complete and closed
- Stage F complete and closed
- Stage G complete and closed
- Stage H complete and closed
- Stage I complete and closed
- Stage J complete and closed
- Stage K complete and closed

## Current Objective

- keep refining the post-Stage-K `AI 热点追踪` surface now that the local Docker dev loop is set up for more stable polling-based hot reload

## Active Task

- none currently fixed; wait for the next bounded task before opening a new active spec

## Current Roadmap Alignment

- Current roadmap theme:
  - `Theme 3: Staged AI Capability Expansion`
- Current roadmap wave:
  - `Wave 2: Connector and Context Plane`
- Interpretation rule:
  - the bounded stage is the execution unit; the roadmap wave remains the broader concept family
- Current baseline:
  - `AI 热点追踪` now has one structured content pipeline, one lightweight all-workspaces entry, one permanent owner-only workspace delete path, one split report plus `追问` layout, one repaired saved-record path that persists empty follow-up collections correctly, and one homepage-mounted auth overlay entry surface

## Verification Status

- Summary:
  - local Docker development now enables polling-based file watching for the backend and frontend, so routine code edits should not require repeated rebuilds
  - `AI 热点追踪` saved-record load no longer requests an invalid limit
  - `/workspaces` is now a real lightweight page instead of a redirect
  - owners can now permanently delete a workspace and its associated data after confirmation
  - the AI hot tracker report path now retries one invalid structured draft before returning an explicit generation failure
  - saving a hot-tracker report now writes `source_set.follow_ups` as a real list at the source path
  - historical saved records have an Alembic backfill that normalizes missing `follow_ups` values to `[]`
  - protected product pages now land on one homepage-mounted auth overlay instead of showing a retained auth-required card or a separate login/register UI

- Last Verified At: 2026-04-17

## Current Blockers

- none inside the repo

## Ready Now

1. keep tightening `AI 热点追踪` report readability, typography, and visual hierarchy
2. keep refining the split surface so the right `追问` module feels like a first-class companion rather than a helper rail
3. decide whether workspace deletion should also be exposed from additional module surfaces beyond `/workspaces`

## Last Completed Task

- `tasks/archive/ai-hot-tracker-report-scroll-and-panel-polish.md`

## Recent Decisions

- `DEC-2026-04-09-130` close Stage K as complete; the next step is a human decision about the next bounded stage rather than another default Stage K follow-through task
- `DEC-2026-04-15-131` simplify the post-Stage-K AI frontier workbench by removing the right rail, hiding analysis-mode switches, deleting separate formal-output actions, and keeping the default user path focused on source intake, one current result, and recent records
- `DEC-2026-04-15-132` rename the visible module from `AI 前沿研究` to `AI 热点追踪`, adopt `AI Signal Tracker` as the English subtitle, and redesign the home plus workbench surfaces around that narrower product identity
- `DEC-2026-04-16-133` start one bounded `AI 热点追踪` content-pipeline rebuild around trusted external source intake, one structured middle layer, and one structured report-generation path
- `DEC-2026-04-17-134` make workspace deletion permanent, owner-only, and explicit
- `DEC-2026-04-17-135` fix saved-record follow-up shape at the write path and normalize historical data
- `DEC-2026-04-17-136` remove the retained auth-required surface from protected product paths and restore the prior path after login
- `DEC-2026-04-17-137` collapse frontend auth into one account-entry surface that auto-registers unknown accounts and signs in existing accounts
- `DEC-2026-04-17-138` move the frontend auth entry onto the homepage as a blocking overlay instead of treating `/login` as the primary product-facing surface
