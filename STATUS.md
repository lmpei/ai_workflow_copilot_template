# Status

Current state only. Keep this file short, current, and action-oriented.

## Metadata

- Last Updated: 2026-04-02

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
- Stage I active

## Current Objective

- execute the first bounded Stage I connector and context-plane wave by delivering one Research-first external-context
  pilot on top of the new connector contract and explicit workspace-consent boundary, while keeping connector failure
  states visible and public product boundaries stable

## Active Task

- `tasks/stage-i-03-research-external-context-pilot.md`

## Verification Status

- Summary: Stage G is complete and closed after the multi-subdomain cutover. The live product stack now runs behind one
  shared Cloudflare -> Caddy edge as `weave.lmpai.online` plus `api.lmpai.online`, while the root homepage lives
  outside this repository. Stage H is now also complete and closed: the shared model-interface foundation is in place,
  one bounded Research tool-assisted path is live, that path has explicit background analysis runs plus compact resumed
  memory, and recent terminal runs now surface one operator-facing regression review baseline. Stage I is now active as
  the next bounded roadmap step: move from internal-only tools toward one connector or context-plane pilot with
  explicit consent, honest degraded behavior, and visible trace boundaries. The first Stage I foundation is now in
  place: the backend has one bounded external-context connector contract plus one workspace-level consent record and API
  surface before any actual external-context call path is enabled.
- Last Verified At: 2026-04-02

## Current Blockers

- none inside the repo

## Assumptions

- module product names remain unchanged for now
- Research remains the reference workflow when module differences and entry explanations are being clarified
- the live public demo remains demo-grade during the first model-interface modernization wave
- the root homepage at `lmpai.online` is now treated as a separate site outside this repository
- this repository should become the dedicated product stack for `weave.lmpai.online` plus `api.lmpai.online`
- the first visible capability pilot should stay bounded to one Research path before any broader module rollout

## Information Gaps

- which single external context source should back the first Research pilot without creating premature connector sprawl

## Ready Now

1. implement `stage-i-03` to make one Research path use approved external context while keeping internal retrieval and
   connector-backed context visibly distinct
2. keep the live `weave` and `api` hosts stable while Stage I extends the Research-first pilot toward external context
3. preserve the current trace and degraded-path honesty baseline as connector capabilities are introduced

## Parked / Later

1. staged AI capability expansion from `docs/prd/LONG_TERM_ROADMAP.md`
2. deeper trust and eval flywheel work beyond the current deployment-boundary split
3. product-name redesign for the three scenario modules

## Last Completed Task

- `tasks/archive/stage-i/stage-i-02-connector-contract-and-consent-foundation.md`

## Recent Decisions

- `DEC-2026-04-01-079` complete `stage-f-17`, tighten workbench density, remove repeated explanation, add drag-and-drop
  plus click-to-select upload, archive the task, and return Stage F to final closeout review
- `DEC-2026-04-01-080` complete `stage-f-18`, reset `/app` into a denser project home and reshape the main workspace
  into a clearer research-workflow page, archive the task, and return Stage F to final closeout review
- `DEC-2026-04-01-081` close Stage F after the final research-workflow reset and open Stage G as the new bounded unit
  for product-only subdomain deployment adaptation
- `DEC-2026-04-01-082` adopt the multi-subdomain target where `lmpai.online` is the separate homepage outside this
  repo, `weave.lmpai.online` is the product frontend, and `api.lmpai.online` is the dedicated API host behind a shared
  Cloudflare -> Caddy edge
- `DEC-2026-04-01-083` close Stage G after the product-only host split is live and this repo now serves only the
  dedicated `weave` frontend plus `api` backend stack
- `DEC-2026-04-01-084` open Stage H as the next bounded unit for model-interface modernization with one tool-visible
  Research pilot and explicit trace/eval honesty
- `DEC-2026-04-01-085` define the first Stage H task wave as the shared model-interface foundation, one bounded
  Research tool-assisted pilot, and tool-visible trace/eval follow-through
- `DEC-2026-04-01-086` complete `stage-h-02`, add the shared model-interface foundation, archive the task, and move
  Stage H to the bounded Research pilot
- `DEC-2026-04-01-087` stop tracking `server/storage/uploads/` in Git, treat upload files as runtime-only state, and
  keep the active Stage H work focused on the Research pilot instead of on local data churn
- `DEC-2026-04-01-088` complete `stage-h-03`, add one bounded Research tool-assisted chat pilot on top of the shared
  model-interface layer, archive the task, and move Stage H to trace/eval visibility follow-through
- `DEC-2026-04-01-089` complete `stage-h-04`, make the Research pilot readable in trace surfaces, add a bounded
  regression baseline for honest degraded-path review, archive the task, and return Stage H to human task-wave
  selection
- `DEC-2026-04-01-090` define the second Stage H task wave as Research-first background analysis runs, bounded
  conversation-state compaction, and tool-aware replay/regression follow-through instead of broadening into connector
  or multi-agent work yet
- `DEC-2026-04-01-091` complete `stage-h-07`, add one explicit Research background analysis run path with visible run
  status and trace linkage, archive the task, and move Stage H to bounded compaction and run-memory follow-through
- `DEC-2026-04-02-092` complete `stage-h-08`, add one bounded resumed-run memory contract on top of Research
  background analysis runs, archive the task, and move Stage H to tool-aware replay/regression follow-through
- `DEC-2026-04-02-093` complete `stage-h-09`, add one operator-visible regression review path for terminal Research
  analysis runs, archive the task, and return Stage H to human selection of the next bounded wave
- `DEC-2026-04-02-094` close Stage H after the full Wave 1 model-interface and built-in-tool baseline is materially
  delivered, and open Stage I as the bounded connector and context-plane pilot stage
- `DEC-2026-04-02-095` define the first Stage I wave as connector-contract foundation, one Research external-context
  pilot, and one connector trace/consent visibility follow-through
- `DEC-2026-04-02-096` complete `stage-i-02`, add one bounded connector contract plus one workspace-level consent API,
  archive the task, and move Stage I to the visible Research external-context pilot
