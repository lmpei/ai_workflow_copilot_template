# Status

Current state only. Keep this file short, current, and action-oriented.

## Metadata

- Last Updated: 2026-04-07

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

- keep the live product hosts stable while moving from the current repo-local out-of-process Research MCP baseline to
  one true external MCP endpoint with explicit transport, auth, and review visibility

## Active Task

- `tasks/stage-i-19-connector-configured-remote-mcp-endpoint-foundation.md`

## Current Roadmap Alignment

- Current roadmap theme:
  - `Theme 3: Staged AI Capability Expansion`
- Current roadmap wave:
  - `Wave 2: Connector and Context Plane`
- Interpretation rule:
  - the active `Stage I` plan is the bounded execution unit; the roadmap wave remains the broader concept family
- Current Wave 2 baseline:
  - one connector-backed Research integration with explicit consent, snapshots, and review is already in place
- Newly delivered:
  - one bounded local MCP server foundation
  - one bounded MCP resource contract wired to the existing Research connector consent boundary
- one real product-facing MCP-backed Research path on the existing `research_external_context` surface
- one MCP-aware trace and operator-review layer on that same visible path
- one true out-of-process MCP client and transport foundation behind the same connector consent boundary
- one visible Research path that now actually reads the bounded out-of-process MCP resource instead of the earlier
  local in-process shortcut
- one remote-MCP-aware trace and operator-review layer on that same visible path
- Still not covered:
  - one true external MCP endpoint outside this repository
  - one bounded Research path that reads a true external MCP resource instead of the current repo-local subprocess
    server
  - one explicit credential and auth boundary around that true external MCP endpoint

## Verification Status

- Summary: Stage G is complete and closed after the multi-subdomain cutover. Stage H is complete and closed after the
  bounded model-interface and tool-visible Research baseline. Stage I has now completed four bounded connector and
  context-plane waves: connector contract plus consent, one visible Research external-context pilot, connector-aware
  trace and review, explicit external-resource snapshots, explicit consent lifecycle plus snapshot selection, one
  resource-aware review baseline, one bounded local MCP contract plus local server foundation, one visible Research
  MCP-backed product path, one MCP-aware trace and operator-review layer on that same path, one true out-of-process
  MCP client and transport foundation behind the same connector boundary, one visible Research path that now actually
  reads the bounded out-of-process MCP resource, and one remote-MCP-aware trace and operator-review layer on that same
  visible path. The current learning gap is no longer repo-local MCP transport; it is one true external MCP endpoint,
  one visible Research path against that endpoint, and one explicit credential/auth plus review baseline around it.
- Last Verified At: 2026-04-07

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

- how far the next Stage I wave should go beyond one true external MCP endpoint before Wave 2 is considered fully
  learned for this repository

## Ready Now

1. execute `stage-i-19` to add one connector-configured true external MCP endpoint foundation without broadening into
   generic multi-server support
2. keep the live `weave` and `api` hosts stable while the Stage I MCP pilot moves from repo-local transport to one
   true external endpoint
3. avoid opening broad MCP sprawl or multi-agent scope before the current bounded Research-first true external MCP
   path is complete

## Parked / Later

1. staged AI capability expansion from `docs/prd/LONG_TERM_ROADMAP.md`
2. deeper trust and eval flywheel work beyond the current deployment-boundary split
3. product-name redesign for the three scenario modules

## Last Completed Task

- `tasks/archive/stage-i/stage-i-17-remote-mcp-trace-and-review-visibility.md`

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
- `DEC-2026-04-02-097` complete `stage-i-03`, add one bounded Research external-context pilot on top of the Stage I
  connector consent boundary, archive the task, and move Stage I to connector trace and consent visibility follow-through
- `DEC-2026-04-02-098` complete `stage-i-04`, make connector consent state, connector use, and degraded outcomes
  readable in operator-facing trace and review surfaces, archive the task, and return Stage I to human selection of the
  next bounded wave
- `DEC-2026-04-02-099` define the second Stage I wave as external resource snapshots, consent lifecycle plus resource
  selection, and resource-aware replay or review follow-through instead of broadening early into generic MCP sprawl or
  multi-agent work
- `DEC-2026-04-02-100` complete `stage-i-06`, persist approved external-context matches as explicit Research external
  resource snapshots, expose those snapshots on chat, runs, and observability surfaces, archive the task, and move
  Stage I to consent lifecycle and resource selection follow-through
- `DEC-2026-04-03-102` complete `stage-i-08`, extend the bounded Research run-review baseline so operators can see
  selected resource snapshots, actual used snapshots, resource-selection mode, and consent-lifecycle consistency
- `DEC-2026-04-03-103` clarify the control-plane distinction between bounded stage completion and roadmap-wave exit
  signals so Stage I closeout and optional MCP follow-through are judged explicitly instead of implicitly
- `DEC-2026-04-03-104` keep Stage I open for one narrow third wave so MCP enters the actual bounded task stack instead
  of remaining only a deferred Wave 2 concept
- `DEC-2026-04-03-105` complete `stage-i-11`, add one bounded local MCP server and MCP resource contract behind the
  existing Research connector consent boundary, archive the task, and move Stage I to one visible Research MCP
  resource-context pilot
- `DEC-2026-04-03-106` complete `stage-i-12`, connect the existing visible Research external-context surface to the
  bounded local MCP resource path, preserve explicit consent and snapshot reuse boundaries, archive the task, and move
  Stage I to MCP trace and review visibility
- `DEC-2026-04-03-110` complete `stage-i-15`, add one true out-of-process MCP client and transport foundation behind
  the existing Research connector consent boundary, archive the task, and move Stage I to the visible remote-MCP
  Research pilot
- `DEC-2026-04-04-111` complete `stage-i-16`, move the visible Research external-context path from the earlier local
  MCP shortcut onto the bounded out-of-process MCP read path, preserve consent and snapshot reuse, archive the task,
  and move Stage I to remote-MCP trace and review visibility
- `DEC-2026-04-07-112` complete `stage-i-17`, make remote-MCP transport, read status, and transport failure readable
  in trace and operator review on the visible Research path
- `DEC-2026-04-07-113` keep Stage I open for one fifth bounded wave so the next work proves one true external MCP
  endpoint instead of stopping at the current repo-local subprocess server baseline
