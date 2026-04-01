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

- continue the first bounded AI-capability wave after the deployment split by using the new shared model interface for
  one visible Research pilot, then preserving honest tool visibility in trace/eval surfaces while the public product
  hosts remain stable

## Active Task

- `tasks/stage-h-03-research-tool-assisted-analysis-pilot.md`

## Verification Status

- Summary: Stage G is complete and closed after the multi-subdomain cutover. The live product stack now runs behind one
  shared Cloudflare -> Caddy edge as `weave.lmpai.online` plus `api.lmpai.online`, while the root homepage lives
  outside this repository. Stage H is now underway: the shared model-interface foundation is in place, and the next
  active work is the first bounded Research pilot on top of that foundation.
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

- which one bounded tool-assisted Research path should become the first visible Stage H pilot after the shared model
  interface lands
- how much of the next model-interface layer should stay provider-neutral versus using one provider-first capability
  path for the first public demoable pilot

## Ready Now

1. choose and implement one bounded Research-first tool-assisted workflow on top of the new shared model interface
2. extend trace/eval surfaces so tool behavior and degraded-output honesty remain visible during the first capability wave
3. keep the live `weave` and `api` hosts stable while the first Research pilot lands

## Parked / Later

1. staged AI capability expansion from `docs/prd/LONG_TERM_ROADMAP.md`
2. deeper trust and eval flywheel work beyond the current deployment-boundary split
3. product-name redesign for the three scenario modules

## Last Completed Task

- `tasks/archive/stage-h/stage-h-02-responses-style-model-interface-foundation.md`

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
