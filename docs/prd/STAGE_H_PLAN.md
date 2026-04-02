# Stage H Plan

## Stage Name

`Stage H: Model Interface Modernization and Tool-Visible Research Pilot`

## Status

- Status: active
- Opened At: 2026-04-01
- First Task Wave: complete
- Second Task Wave: active

## Position In The Project

Stage H begins after the closeout of Stage G. Stage G corrected the deployment boundary so this repository now serves
only the dedicated product frontend and backend hosts behind one shared edge. With that boundary now stable, the next
bounded stage should return to the long-term roadmap and begin the first post-split capability wave instead of
continuing deployment work.

## Stage Goal

Modernize the model-facing interface in one bounded way so the product can support more capable tool-assisted behavior
without losing the current public-demo honesty or shared-platform shape.

## Primary Outcome

The repository should gain:

- one clearer shared model interface that can express modern request and response behavior
- one bounded Research-first tool-assisted workflow on top of that interface
- one explicit trace and eval baseline that shows tool behavior honestly instead of hiding it behind generic outputs

## Planning Model

Stage H continues to operate under the same three-track roadmap model:

1. `Research`
2. `Platform Reliability`
3. `Delivery and Operations`

## Priority Model

- Primary track:
  - `Research`, because the first pilot should stay bounded to one visible Research path
- Required parallel tracks:
  - `Platform Reliability`, so tool behavior remains observable, replayable, and quality-checkable
  - `Delivery and Operations`, so the live product hosts stay stable while the capability layer changes

## Track 1: Research

### Objective

Use Research as the reference workflow for the first model-interface modernization wave.

### Focus Areas

- choose one visible Research path for the first tool-assisted pilot
- keep the pilot useful to the public product instead of hiding it in a purely internal experiment
- avoid broad multi-module rollout before one workflow is stable and understandable

### Expected Outcomes

- one Research path can show modern tool-assisted analysis behavior
- the user can distinguish normal grounded interaction from the new tool-assisted path

## Track 2: Platform Reliability

### Objective

Keep tool behavior explicit in traces, evals, and degraded outputs.

### Focus Areas

- preserve current trace honesty while the model interface changes
- expose tool requests, tool results, and degraded-output paths where they matter
- keep the new interface provider-aware but not tightly coupled to one accidental implementation detail

### Expected Outcomes

- tool behavior remains explainable
- the first capability wave ships with visible quality and trace follow-through

## Track 3: Delivery and Operations

### Objective

Keep the stable multi-subdomain deployment boundary intact while the capability layer changes.

### Focus Areas

- do not break `weave.lmpai.online` or `api.lmpai.online`
- avoid deployment drift between env templates, service contracts, and docs
- keep the public product usable while the first capability pilot is introduced

### Expected Outcomes

- the product-only host split remains stable
- capability work does not regress the current deployment baseline

## Non-Goals

Stage H does not primarily optimize for:

- connector or MCP integration waves
- multi-agent planner/worker orchestration
- realtime or multimodal interaction
- unconstrained built-in-tool rollout across every module at once
- module-name redesign
- another deployment-boundary refactor

## Execution Rules

- Stage H tasks should use `stage-h-*` naming
- keep Research as the first bounded pilot before expanding to Support or Job
- do not hide tool behavior behind generic success-only summaries
- preserve the current public product and shared runtime boundaries while modernizing the model interface

## Success Criteria

Stage H is successful when:

- one shared model-interface foundation exists behind the current product hosts
- one Research workflow visibly uses the new interface in a bounded, demoable way
- tool behavior appears in traces and eval-facing surfaces honestly enough to support later capability waves

## First Task Wave

The first executable Stage H wave is:

1. `tasks/archive/stage-h/stage-h-02-responses-style-model-interface-foundation.md` (complete)
2. `tasks/archive/stage-h/stage-h-03-research-tool-assisted-analysis-pilot.md` (complete)
3. `tasks/archive/stage-h/stage-h-04-tool-trace-and-eval-visibility.md` (complete)

## Completed So Far

- `tasks/archive/stage-h/stage-h-02-responses-style-model-interface-foundation.md`
- `tasks/archive/stage-h/stage-h-03-research-tool-assisted-analysis-pilot.md`
- `tasks/archive/stage-h/stage-h-04-tool-trace-and-eval-visibility.md`
- `tasks/archive/stage-h/stage-h-07-research-background-analysis-runs.md`
- `tasks/archive/stage-h/stage-h-08-research-context-compaction-and-run-memory.md`

The repository now has one shared backend model-interface layer beneath chat generation, embeddings, and eval judging.
The repository also now has one bounded Research tool-assisted chat pilot on top of that layer: the main Research chat
surface can switch into a pilot mode that plans a bounded analysis focus, invokes existing workspace tools inline, and
returns visible tool-step summaries alongside the grounded answer. That pilot now also has one honest visibility
follow-through: recent traces surface the planning focus, search query, visible tool steps, and degraded-path reason,
while the backend has one bounded regression baseline for visible tool steps plus honest no-source degradation.

The second wave has now deepened that path twice: Research workspaces can launch one explicit background analysis
run, watch it move through queued, running, completed, degraded, or failed state, and receive the resulting answer,
tool steps, and trace linkage back on the same workspace surface. That run path now also supports one bounded
resumed-run memory contract so later passes in the same conversation can carry forward one compact prior summary
without growing prompt state unboundedly.

## Second Task Wave
The second executable Stage H wave is now:

1. `tasks/archive/stage-h/stage-h-07-research-background-analysis-runs.md` (complete)
2. `tasks/archive/stage-h/stage-h-08-research-context-compaction-and-run-memory.md` (complete)
3. `tasks/stage-h-09-tool-aware-replay-and-regression-baseline.md`

### Why This Wave Exists

The first Stage H wave proved that one visible Research-first tool-assisted path can exist honestly on the main product
surface. `stage-h-07` completed the first deepening step by turning that path into one explicit background-capable run
with persisted run state, assistant answer delivery, and trace linkage. `stage-h-08` then added one bounded
resumed-run memory contract on top of that path. The remaining bounded learning step should not broaden into another
module or leap into connectors or multi-agent handoffs. It should deepen that one visible path so the repository
learns:
- how replay and regression should validate a resumed bounded run instead of a one-shot tool-assisted answer
- which visible trace or run-memory fields are durable enough to support honest operator review and replay
- how the repository should measure regression once tool-assisted analysis has both background execution and compacted
  memory continuity
