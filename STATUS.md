# Status

Current state only. Keep this file short, current, and action-oriented.

## Metadata

- Last Updated: 2026-04-01

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
- Stage H active

## Current Objective

- complete the first bounded Stage H capability wave, keep the visible Research tool-assisted pilot honest in traces
  and regression review, and wait for the next bounded Stage H task wave definition while the public product hosts
  remain stable

## Active Task

- none; first Stage H task wave complete and awaiting the next bounded task definition

## Verification Status

- Summary: Stage G is complete and closed after the multi-subdomain cutover. The live product stack now runs behind one
  shared Cloudflare -> Caddy edge as `weave.lmpai.online` plus `api.lmpai.online`, while the root homepage lives
  outside this repository. Stage H is now underway: the shared model-interface foundation is in place, one bounded
  Research tool-assisted chat pilot is live behind the Research workspace surface, and the first Stage H wave now also
  has trace-visible tool steps plus a bounded regression baseline for honest pilot review.
- Last Verified At: 2026-04-01

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

- which next bounded Stage H capability step should follow the first Research pilot wave without jumping too early into
  connector or multi-agent work
- whether the next Stage H wave should deepen Research first or broaden the new model-interface layer into another
  user-visible module path

## Ready Now

1. define the next bounded Stage H task wave now that the first foundation / pilot / visibility sequence is complete
2. keep the live `weave` and `api` hosts stable while the next capability wave is being selected
3. preserve the current honest pilot visibility baseline instead of hiding it behind generic success language

## Parked / Later

1. staged AI capability expansion from `docs/prd/LONG_TERM_ROADMAP.md`
2. deeper trust and eval flywheel work beyond the current deployment-boundary split
3. product-name redesign for the three scenario modules

## Last Completed Task

- `tasks/archive/stage-h/stage-h-04-tool-trace-and-eval-visibility.md`

## Recent Decisions

- `DEC-2026-03-31-078` complete `stage-f-16`, finish the final Stage F visual redesign and cleanup pass, archive the
  task, and return the stage to human closeout review
- `DEC-2026-03-31-079` complete `stage-f-17`, tighten workbench density, remove repeated explanation, add drag-and-drop
  plus click-to-select upload, archive the task, and return Stage F to final closeout review
- `DEC-2026-03-31-080` complete `stage-f-18`, reset `/app` into a denser project home and reshape the main workspace
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
