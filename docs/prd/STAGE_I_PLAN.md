# Stage I Plan

## Stage Name

`Stage I: Connector and Context Plane Pilot`

## Status

- Status: active
- Opened At: 2026-04-02
- First Task Wave: complete

## Position In The Project

Stage I begins after the closeout of Stage H. Stage H delivered the first bounded model-interface and built-in-tool
baseline on the product hosts. With that baseline now stable enough to inspect and review, the next bounded roadmap
step should move from internal-only tools toward one connector and context-plane pilot rather than jumping early into
multi-agent orchestration.

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

The next Stage I step is not yet fixed. The first bounded wave is complete and ready for human selection of the next
connector or context-plane follow-through.
