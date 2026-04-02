# Stage I Plan

## Stage Name

`Stage I: Connector and Context Plane Pilot`

## Status

- Status: active
- Opened At: 2026-04-02
- First Task Wave: complete
- Second Task Wave: complete
- Third Task Wave: active

## Position In The Project

Stage I begins after the closeout of Stage H. Stage H delivered the first bounded model-interface and built-in-tool
baseline on the product hosts. With that baseline now stable enough to inspect and review, the next bounded roadmap
step should move from internal-only tools toward one connector and context-plane pilot rather than jumping early into
multi-agent orchestration.

## Roadmap Alignment

- Roadmap theme:
  - `Theme 3: Staged AI Capability Expansion`
- Roadmap wave:
  - `Wave 2: Connector and Context Plane`
- Stage-I interpretation:
  - this plan defines the bounded execution unit for one connector-backed baseline
- Wave interpretation:
  - Wave 2 remains the broader concept family; Stage I closeout does not require exhausting every Wave 2 concept
- Current Stage-I baseline:
  - one connector-backed Research integration with explicit consent, resource snapshots, and operator review
  - one bounded local MCP server and MCP resource contract behind that same Research-first permission model
  - one visible Research MCP-backed product path that reuses that same consent and snapshot model
- Still optional follow-through:
  - MCP trace and review visibility on that visible path
  - most MCP breadth beyond the first bounded path
  - broader connector rollout outside the same Research-first surface

## Stage Goal

Introduce one external context source into the product in a bounded, Research-first way, with explicit consent,
connector-visible traces, and honest degraded behavior.

## Primary Outcome

The repository should gain:

- one clearer connector or context-plane contract on top of the current product stack
- one bounded Research-first external-context pilot that stays publicly demonstrable
- one explicit trace, consent, and degraded-path baseline around that pilot

## Planning Model

Stage I continues to operate under the same three-track roadmap model:

1. `Research`
2. `Platform Reliability`
3. `Delivery and Operations`

## Priority Model

- Primary track:
  - `Research`, because the first connector pilot should stay bounded to one visible Research path
- Required parallel tracks:
  - `Platform Reliability`, so consent, trace, and degraded-path behavior stay explicit
  - `Delivery and Operations`, so the live `weave` and `api` hosts remain stable while one external context source is
    introduced

## Track 1: Research

### Objective

Use Research as the reference workflow for the first external-context pilot.

### Focus Areas

- choose one bounded external context source instead of broad connector sprawl
- keep the pilot visible on the main Research surface instead of hiding it in a purely internal experiment
- preserve the distinction between internal retrieval and external context access

### Expected Outcomes

- one Research path can draw from an approved external context source
- the user can tell when the product is using internal workspace material versus approved external context

## Track 2: Platform Reliability

### Objective

Keep consent, connector visibility, and degraded behavior explicit.

### Focus Areas

- define a stable connector contract before broadening integrations
- make connector use appear clearly in traces and operator review
- preserve honest degraded behavior when external context is unavailable, denied, or incomplete

### Expected Outcomes

- the first connector pilot remains explainable
- failure, denial, and no-data cases stay inspectable instead of collapsing into generic fallback behavior

## Track 3: Delivery and Operations

### Objective

Keep the stable multi-subdomain deployment boundary intact while external context capabilities are introduced.

### Focus Areas

- do not break `weave.lmpai.online` or `api.lmpai.online`
- avoid deployment drift between env contracts, connector settings, and docs
- keep the public product usable even when the external context pilot is unavailable

### Expected Outcomes

- the product-only host split remains stable
- connector work does not regress the current deployment baseline

## Non-Goals

Stage I does not primarily optimize for:

- a generic connector marketplace
- multiple external integrations at once
- full MCP platform breadth across every module
- multi-agent handoffs or planner-worker orchestration
- realtime or multimodal interaction
- product-name redesign

## Execution Rules

- Stage I tasks should use `stage-i-*` naming
- keep the first connector pilot bounded to Research before expanding to Support or Job
- do not hide connector usage behind generic success-only summaries
- preserve the current public product and shared runtime boundaries while adding external context

## Success Criteria

Stage I is successful when:

- one connector or context-plane contract exists behind the current product hosts
- one Research workflow visibly uses one bounded external context source with explicit consent
- connector behavior appears in traces and review-facing surfaces honestly enough to support later capability waves
- this bounded stage can be judged complete without claiming exhaustive MCP coverage, because the roadmap wave uses a
  minimum exit signal rather than a full concept checklist

## First Task Wave

The first executable Stage I wave is:

1. `tasks/archive/stage-i/stage-i-02-connector-contract-and-consent-foundation.md` (complete)
2. `tasks/archive/stage-i/stage-i-03-research-external-context-pilot.md` (complete)
3. `tasks/archive/stage-i/stage-i-04-connector-trace-and-consent-visibility.md` (complete)

### Why This Wave Exists

Stage H already answered how one bounded internal tool-assisted path should look. Stage I should answer the next
learning question from the roadmap without broadening too early:

- how external context should enter the system through one explicit contract
- where consent and permission review should live
- how connector use, denial, and no-data degradation should appear in traces and review surfaces

This wave should stay narrow: one visible Research-first connector pilot, one consent boundary, and one honest review
layer before any broader MCP or orchestration work opens.

## Current Progress

- complete: `stage-i-02`, which established one bounded connector definition plus one explicit workspace-level consent
  record and API for the Research-first pilot
- complete: `stage-i-03`, which connected one bounded external context source to the main Research workflow while
  keeping internal workspace evidence and connector-backed context visibly distinct and honest under denied or
  unavailable conditions
- complete: `stage-i-04`, which made connector consent state, connector use, external-match visibility, and degraded
  outcomes readable in trace and operator-facing review surfaces
- complete: `stage-i-06`, which persisted approved external-context matches as explicit Research external-resource
  snapshots, linked direct chat and background analysis runs to the snapshot they used, and surfaced recent snapshots
  back on the main product and observability views
- complete: `stage-i-07`, which made consent changes and explicit snapshot selection more inspectable on that same
  bounded Research path
- complete: `stage-i-08`, which made replay or review aware of selected snapshots, actual used snapshots,
  resource-selection mode, and consent-lifecycle consistency on that same bounded Research path
- complete: `stage-i-11`, which added one bounded local MCP server and one MCP resource contract behind the existing
  Research connector consent boundary
- complete: `stage-i-12`, which connected the existing visible Research external-context surface to the bounded local
  MCP resource foundation while preserving explicit consent, snapshot reuse, and honest degraded behavior
- active now: `stage-i-13`, which will make MCP use and degraded outcomes readable in trace and operator-review
  surfaces on that same bounded Research path
## Second Task Wave

The second executable Stage I wave is:

1. `tasks/archive/stage-i/stage-i-06-research-external-resource-snapshots.md`
2. `tasks/archive/stage-i/stage-i-07-consent-lifecycle-and-resource-selection.md`
3. `tasks/archive/stage-i/stage-i-08-resource-aware-replay-and-review-baseline.md`

### Why This Wave Exists

The first Stage I wave answered the basic connector questions:

- one explicit connector contract
- one explicit consent boundary
- one visible external-context pilot
- one connector-aware review surface

The next Wave 2 learning question is narrower and more structural:

- when approved external context should become an explicit reusable resource instead of a hidden transient input
- where consent lifecycle and resource selection should live before broader MCP work opens
- how replay and review should change once external context becomes more resource-like

This wave should stay inside the same Research-first pilot instead of broadening into multiple connectors or broader
module rollout.

### Current Second-Wave Outcome

The second Stage I wave is now complete:

- approved external-context matches can persist as explicit Research resource snapshots
- direct chat and background analysis runs can now distinguish selected snapshots from actual used snapshots
- consent lifecycle is explicit enough for the bounded connector pilot to support grant, revoke, and honest degraded behavior
- recent terminal connector-backed runs now expose one resource-aware review baseline instead of relying only on raw trace inspection

### Remaining Optional Follow-Through

These items are still valid future work, but they are not required to treat the current Stage I connector-backed
baseline as delivered:

- broader MCP breadth after the first bounded path is proven
- broader connector rollout outside the same bounded Research-first path

## Third Task Wave

The third executable Stage I wave is:

1. `tasks/archive/stage-i/stage-i-11-mcp-contract-and-local-server-foundation.md`
2. `tasks/archive/stage-i/stage-i-12-research-mcp-resource-context-pilot.md`
3. `tasks/stage-i-13-mcp-trace-and-review-visibility.md`

### Why This Wave Exists

The first two Stage I waves already answered the bounded connector questions:

- one explicit connector contract
- one explicit consent boundary
- one visible external-context pilot
- one explicit resource and review layer

But MCP has still not entered the actual task stack. This third wave keeps Stage I open only long enough to answer the
next narrower Wave 2 question:

- how one explicit MCP server or resource contract should appear in this repo
- how that MCP path should stay bounded to one Research-first product surface
- how MCP use should stay visible in trace and review instead of appearing as a hidden transport detail

This wave should still avoid generic MCP sprawl, broad connector marketplaces, or multi-module rollout.
