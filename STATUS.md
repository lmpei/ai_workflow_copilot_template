# Status

Current state only. Keep this file short, current, and action-oriented.

## Metadata

- Last Updated: 2026-04-21

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

- focus current execution on `AI 热点追踪` as one real single-agent tracking product: persistent workspace profile, durable tracking runs, grounded follow-up, and one canonical release path guarded by `CI -> deploy`

## Active Task

- `tasks/ai-hot-tracker-ranking-and-delta-decision-layer.md`

## Current Roadmap Alignment

- Current roadmap theme:
  - `Theme 3: Staged AI Capability Expansion`
- Current roadmap wave:
  - `Wave 2: Connector and Context Plane`
- Interpretation rule:
  - the bounded stage is the execution unit; the roadmap wave remains the broader concept family
- Current baseline:
  - `AI 热点追踪` now has one fixed content chain: trusted source intake -> normalized source items -> schema-bound report synthesis -> run-bound follow-up grounding
  - `AI 热点追踪` workspaces now carry one default `tracking_profile`, and the backend now persists durable `ai_hot_tracker_tracking_run` state with delta summary, source payloads, degraded or failed honesty, and follow-up thread history
  - `Support Copilot` and `Job Assistant` remain visible in the product frame, but active implementation focus is intentionally frozen onto the first module until the hot-tracker agent loop is stronger
  - backend `ruff` now passes again on the active branch, and blocked production deploys now write a clear GitHub Actions summary that points back to the failed upstream `CI` run

## Verification Status

- Summary:
  - local Docker development still uses polling-based hot reload for backend and frontend edits
  - weave production still deploys through the repo-owned `CI -> deploy` path with retry and rollback visibility
  - `AI 热点追踪` now exposes manual run creation, run listing, run fetch, run delete, and run-bound follow-up on top of the new tracking-run persistence layer
  - the hot-tracker frontend now reads durable runs directly instead of depending on an optional save-first report path
  - owners can permanently delete a workspace and its associated data after confirmation
  - protected product pages still use the homepage-mounted auth overlay instead of a separate auth page
  - local and deployed environments both enter through the same canonical workspace path without public-demo bootstrap behavior

- Last Verified At: 2026-04-21

## Current Blockers

- none inside the repo

## Ready Now

1. add ranking, authority, freshness, and novelty scoring before report synthesis so the agent stops behaving like a time-ordered summarizer
2. add clustering and temporal diff so each run compares event groups rather than raw item URLs
3. add scheduled execution plus notify-or-suppress decisions on top of the current manual run baseline

## Last Completed Task

- `tasks/archive/ai-hot-tracker-tracking-agent-foundation.md`

## Recent Decisions

- `DEC-2026-04-17-138` move the frontend auth entry onto the homepage as a blocking overlay instead of treating `/login` as the primary product-facing surface
- `DEC-2026-04-18-139` automate weave production deploys through one repo-owned deploy script, one fixed server wrapper, and one GitHub Actions SSH workflow
- `DEC-2026-04-18-140` give weave deploy failures one explicit retry and rollback path
- `DEC-2026-04-20-141` retire the legacy public-demo runtime entry path and converge local plus deployed environments onto one canonical workspace flow
- `DEC-2026-04-20-142` keep `CI -> deploy` as the production gate and make blocked deploys explicit when upstream CI fails
- `DEC-2026-04-21-143` focus active productization on `AI 热点追踪` as one workspace-level continuous tracking agent with durable runs and grounded follow-up
