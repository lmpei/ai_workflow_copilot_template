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
- Stage G active

## Current Objective

- adapt this repository to the new multi-subdomain deployment model so the repo becomes the dedicated
  `weave.lmpai.online` product plus `api.lmpai.online` backend stack behind a shared Cloudflare -> Caddy edge, while
  the root `lmpai.online` homepage moves outside this repository

## Active Task

- `tasks/stage-g-02-weave-subdomain-product-split.md`

## Verification Status

- Summary: Stage E is complete. Stage F is also complete and closed after the root/home split, the conversation-first
  workbench reset, and the final research-workflow refinement. The new active work is Stage G, which prepares the repo
  for a product-only deployment boundary at `weave.lmpai.online` plus `api.lmpai.online`.
- Last Verified At: 2026-04-01

## Current Blockers

- none inside the repo

## Assumptions

- module product names remain unchanged for now
- Research remains the reference workflow when module differences and entry explanations are being clarified
- the live public demo remains demo-grade during the deployment-boundary transition
- the root homepage at `lmpai.online` is now treated as a separate site outside this repository
- this repository should become the dedicated product stack for `weave.lmpai.online` plus `api.lmpai.online`

## Information Gaps

- whether the repo should keep any compatibility path for the older `app.lmpai.online` host during the cutover
- whether the shared edge will be deployed as one host-level Caddy service or as a separate reverse-proxy stack

## Ready Now

1. adapt the frontend entry routes so this repo treats `/` as the canonical product home on `weave.lmpai.online`
2. add a shared-edge deployment path with product and API hosts split behind Caddy
3. update env, CORS, and reverse-proxy expectations so deployment docs and templates no longer assume `app.<domain>`

## Parked / Later

1. staged AI capability expansion from `docs/prd/LONG_TERM_ROADMAP.md`
2. deeper trust and eval flywheel work beyond the current deployment-boundary split
3. product-name redesign for the three scenario modules

## Last Completed Task

- `tasks/archive/stage-g/stage-g-01-task-stack-planning.md`

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
