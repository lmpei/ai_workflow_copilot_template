# Status

Current state only. Keep this file short, current, and action-oriented.

## Metadata

- Last Updated: 2026-04-26

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

- keep `AI hot tracker` stable as the first real single-agent product loop for mainstream AI users: allowlisted source intake, impact-oriented signal judgment, brief-style report output, grounded follow-up, richer runtime truth, internal evaluation visibility, one clean UTF-8 Chinese contract, and one canonical release path guarded by `CI -> deploy`
- treat `docs/prd/AI_HOT_TRACKER_FINAL_DEFINITION.md` as the long-form source of truth for the module's end-state product definition

## Active Task

- none currently; the hot-tracker final stabilization slice is complete and the next bounded slice is waiting on human direction

## Current Roadmap Alignment

- Current roadmap theme:
  - `Theme 3: Staged AI Capability Expansion`
- Current roadmap wave:
  - `Wave 2: Connector and Context Plane`
- Interpretation rule:
  - the bounded stage is the execution unit; the roadmap wave remains the broader concept family
- Current baseline:
  - `AI hot tracker` now has one fixed content chain: trusted source intake -> normalized source items -> ranked and clustered signal candidates -> schema-bound report synthesis -> run-bound follow-up grounding
  - `AI hot tracker` workspaces carry one default `tracking_profile`, and the backend persists durable `ai_hot_tracker_tracking_run` plus `ai_hot_tracker_tracking_state` records for report history, cluster snapshots, notify pointers, due times, and failure memory
  - the hot-tracker backend now adds one bounded decision layer before synthesis: fixed authority, freshness, novelty, and relevance scoring, conservative signal clustering, cluster-based delta comparison, and stable priority or notify decisions
  - the hot-tracker source layer now uses one fixed allowlist across official labs, product updates, developer tooling, research feeds, open-source releases, and selected media feeds; media pages stay list-level only and do not trigger full-article crawling
  - the hot-tracker decision layer now weights actual user impact alongside novelty, freshness, authority, and relevance so the brief reads like a judgment surface instead of a time-sorted digest
  - scheduled hot-tracker evaluation now runs through the worker on a fixed 15-minute sweeper, while steady-state automatic scans update tracking state without saving noisy duplicate runs
  - the hot-tracker control loop now keeps one durable `ai_hot_tracker_signal_memory` layer so signals persist beyond the previous snapshot and can reappear as continuing or cooling event memory instead of stateless URLs
  - the hot-tracker product path now renders one brief-style report contract with `headline`, `summary`, `signals`, `keep_watching`, and lightweight source anchors instead of the older research-style output contract
  - the hot-tracker brief contract now also carries `confidence` plus `blindspots` so the report can state both what it believes and what still needs confirmation
  - the hot-tracker workspace surface now exposes a consumer-facing brief plus follow-up layout, one runtime summary strip, a minimal profile editor for cadence, enabled categories, and alert threshold, a saved-run history drawer, and one run-bound follow-up column
  - the hot-tracker module now also exposes one internal evaluation path so ranking, clustering, delta decisions, source failures, event memory, and brief output quality can be inspected without turning the consumer UI into a debug console
  - the hot-tracker implementation now records one bounded internal agent-role trace (`Scout`, `Resolver`, `Analyst`, `Editor`, `Evaluator`, `Follow-up`) for evaluation reads without exposing those terms on the consumer path
  - the hot-tracker canonical path is now cleaner: the `/ai-hot-tracker/report` alias resolves directly onto tracking-run creation, run-bound follow-up reads one cleaned context contract, and the workspace surface no longer carries broken consumer-facing copy
  - the hot-tracker runtime state now exposes the latest saved brief timestamp plus the latest meaningful-update timestamp instead of relying only on saved-run presence
  - the hot-tracker event-memory layer now tracks streak count, cooling windows, and replacement linkage so continuing and superseded signals can be inspected explicitly
  - saved hot-tracker follow-up answers now persist bounded grounding metadata, and evaluation reads now return machine-readable quality checks for judgment alignment
  - the hot-tracker brief generation path now uses one clean Chinese prompt and fallback contract, and the schema defaults no longer leak damaged copy into degraded or legacy output paths
  - the hot-tracker backend now also carries one fixed replay corpus plus one judgment-calibration suite so official/media/open-source/research ranking, conservative clustering, steady-state suppression, threshold-driven notify, and replacement memory can be replayed without guessing from live traffic
  - the hot-tracker internal evaluation surface now also reads that replay suite directly, so offline calibration is visible alongside the selected run instead of living only in tests
  - the hot-tracker run-evaluation layer now also checks whether the saved brief stays aligned with delta and cluster-level judgment, including change-state honesty, high-priority coverage, single-cluster consistency, and priority or change-type alignment
  - the hot-tracker schema defaults, replay findings, follow-up prompt chain, and task control-plane docs now use one clean UTF-8 Chinese contract instead of mixed damaged strings
  - the long-form end-state definition for `AI hot tracker` now lives in `docs/prd/AI_HOT_TRACKER_FINAL_DEFINITION.md`, while the older frontier-research contract remains a historical pointer only
  - `Support Copilot` and `Job Assistant` remain visible in the product frame, but active implementation focus is intentionally frozen onto the first module until the hot-tracker agent loop is stronger
  - backend `ruff` now passes again on the active branch, and blocked production deploys now write a clear GitHub Actions summary that points back to the failed upstream `CI` run
  - the latest `main` branch lint regression that blocked `Deploy Weave` has been cleared locally, with backend lint plus full backend regression passing again before repush

## Verification Status

- Summary:
  - local Docker development still uses polling-based hot reload for backend and frontend edits
  - weave production still deploys through the repo-owned `CI -> deploy` path with retry and rollback visibility
  - `AI hot tracker` now exposes manual run creation, scheduled sweeper evaluation, run listing, run fetch, run delete, and run-bound follow-up on top of the durable tracking-run persistence layer
  - the hot-tracker backend now persists `ai_hot_tracker_tracking_state` so automatic steady-state scans can update memory without saving noisy duplicate runs
  - report generation now consumes ranked and clustered signal candidates and writes the brief-oriented hot-tracker contract instead of the older research-oriented contract
  - the hot-tracker frontend now reads durable runs directly, shows a consumer-facing brief plus follow-up surface, exposes runtime state and internal evaluation when requested, allows bounded profile edits for cadence, enabled categories, and alert threshold, shows persisted follow-up grounding summaries, and uses one cleaned Chinese copy set across runtime, evaluation, history, and settings
  - the backend now has one deterministic hot-tracker replay suite that can re-run core judgment scenarios locally before someone retunes scoring, clustering, delta, or event-memory logic
  - the internal evaluation view now also reads one replay-evaluation endpoint so offline calibration failures can be seen without leaving the product shell
  - run evaluation now also surfaces deterministic brief-alignment failures instead of only source grounding or blindspot honesty checks
  - owners can permanently delete a workspace and its associated data after confirmation
  - protected product pages still use the homepage-mounted auth overlay instead of a separate auth page
  - local and deployed environments both enter through the same canonical workspace path without public-demo bootstrap behavior
  - verification now includes full backend regression plus frontend verify for the final hot-tracker stabilization pass

- Last Verified At: 2026-04-26

## Current Blockers

- none inside the repo

## Ready Now

1. decide whether the next bounded investment is more hot-tracker judgment tuning or the first implementation slice of the second module
2. if the first module continues, use the replay corpus and replay-evaluation surface to tune impact, novelty, notify, and replacement behavior
3. after the repush, confirm that GitHub `CI -> Deploy Weave` has reached production before starting the next bounded slice

## Last Completed Task

- `tasks/archive/fix-ci-and-unblock-weave-deploy.md`

## Recent Decisions

- `DEC-2026-04-17-138` move the frontend auth entry onto the homepage as a blocking overlay instead of treating `/login` as the primary product-facing surface
- `DEC-2026-04-18-139` automate weave production deploys through one repo-owned deploy script, one fixed server wrapper, and one GitHub Actions SSH workflow
- `DEC-2026-04-18-140` give weave deploy failures one explicit retry and rollback path
- `DEC-2026-04-20-141` retire the legacy public-demo runtime entry path and converge local plus deployed environments onto one canonical workspace flow
- `DEC-2026-04-20-142` keep `CI -> deploy` as the production gate and make blocked deploys explicit when upstream CI fails
- `DEC-2026-04-21-143` focus active productization on `AI hot tracker` as one workspace-level continuous tracking agent with durable runs and grounded follow-up
- `DEC-2026-04-21-144` add one bounded hot-tracker decision layer with ranking, clustering, cluster-based delta, tracking-state memory, and scheduled evaluation
- `DEC-2026-04-21-145` close `AI hot tracker` onto one brief-style product loop with runtime state visibility and an internal evaluation view
- `DEC-2026-04-23-146` position `AI hot tracker` as one mainstream AI brief product with allowlisted source families, impact-oriented signal judgment, and a consumer-facing brief plus follow-up surface
- `DEC-2026-04-24-147` define `AI hot tracker` as one strong-agent product with event memory, internal role traces, and a clean brief-plus-follow-up workspace surface
- `DEC-2026-04-24-148` collapse hot-tracker legacy response branches and broken copy onto one canonical tracking-run and product-copy path
- `DEC-2026-04-24-149` harden hot-tracker runtime truth with durable follow-up grounding, explicit event-memory continuity fields, and machine-readable judgment checks
- `DEC-2026-04-24-150` normalize hot-tracker brief generation and schema defaults onto one clean UTF-8 Chinese contract
- `DEC-2026-04-24-151` add a fixed hot-tracker replay corpus and judgment-calibration suite for offline inspection
- `DEC-2026-04-24-152` expose replay calibration on the internal hot-tracker evaluation surface
- `DEC-2026-04-24-153` make hot-tracker run evaluation judge brief alignment against delta and cluster-level decisions
- `DEC-2026-04-25-154` close hot-tracker stabilization by normalizing UTF-8 Chinese copy and archiving the final completion-line task
- `DEC-2026-04-25-155` make `docs/prd/AI_HOT_TRACKER_FINAL_DEFINITION.md` the long-form source of truth for the module end state
