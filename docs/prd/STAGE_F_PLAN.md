# Stage F Plan

## Stage Name

`Stage F: Public Demo Experience Clarification and UX Reset`

## Status

- Status: active
- Opened At: 2026-03-28
- First Task Wave: active

## Position In The Project

Stage F begins after the closeout of Stage E. Stage E proved that the platform can persist Support cases and Job
hiring packets as real workbench objects, and that the public demo can explain when to start from a fresh guided
workspace versus when to continue from an existing workbench object. Stage F narrows the next bounded step to the
user-facing problem that remains: the public demo and workspace surface still feel too much like an internal platform
console instead of a clear product experience.

## Planning Model

Stage F continues to operate under the same three-track roadmap model:

1. `Research`
2. `Platform Reliability`
3. `Delivery and Operations`

The tracks remain parallel, but Stage F shifts the emphasis again. Delivery and Operations now becomes the primary
track because the main goal is to make the public-facing and workspace-facing experience easier to understand without
hiding real platform behavior.

## Priority Model

- Primary track:
  - `Delivery and Operations` as the user-facing surface and demo-experience reset layer
- Required parallel tracks:
  - `Platform Reliability` to keep persistent workbench state honest and visible during the UX reset
  - `Research` as the reference workflow when the front-end needs to explain why the three modules are different

Stage F should not optimize for new AI capability waves if those waves delay the information-architecture reset or
increase first-time user confusion.

## Stage Goal

Turn the public demo and workspace surface into a clearer product experience with lower cognitive load, explicit page
hierarchy, stronger module differentiation, and a more showcase-ready visual baseline, while preserving the real
Support case and Job hiring-packet behavior introduced in Stage E.

## Track 1: Research

### Objective

Keep Research as the reference workflow so Stage F clarifies real module differences instead of flattening the product
into three generic text-analysis surfaces.

### Focus Areas

- preserve the deepest document-heavy reference workflow while simplifying the front-end
- explain how Research differs from Support and Job without renaming the module products
- keep the module surface honest about work objects, primary outputs, and when each module should be used

### Expected Outcomes

- the front-end can explain why Research exists separately from Support and Job
- module differentiation becomes visible earlier than the deep task or workbench surfaces

## Track 2: Platform Reliability

### Objective

Keep Stage E workbench state and continuity behavior intact while the user-facing structure is simplified.

### Focus Areas

- preserve Support case and Job hiring-packet continuity while front-end entry surfaces change
- avoid fake resets, hidden state loss, or misleading simplification
- keep the workbench objects and shared runtime boundaries visible where they matter

### Expected Outcomes

- the UX reset does not hide or invalidate real platform state
- users can still continue real Support and Job work from the correct workbench object

## Track 3: Delivery and Operations

### Objective

Reduce first-time user confusion and make the live public demo easier to understand, navigate, and present.

### Focus Areas

- home-page and workspace-center information architecture
- workspace hierarchy, navigation, and return paths
- clearer module entry messaging and workbench-first entry rules
- visual polish on the highest-traffic pages after structural simplification lands

### Expected Outcomes

- first-time users can identify where to start
- workspace navigation feels like a hierarchy instead of a flat tool list
- the public demo looks intentional enough for external showcase use

## Non-Goals

Stage F does not primarily optimize for:

- renaming the three scenario modules
- new MCP, realtime, or computer-use capability waves
- deeper Support or Job backend workbench expansion beyond the Stage E baseline
- production-grade multi-tenant SaaS polish
- hidden simplification that conceals real continuity, demo limits, or operator boundaries

## Execution Rules

- Stage F tasks should use `stage-f-*` naming
- solve structure before solving visual polish
- do not hide important state behind misleading simplification
- keep the live public demo honest about what is demo-grade versus durable
- prefer fewer, clearer entry points over exposing every platform surface at once

## Success Criteria

Stage F is successful when:

- a first-time user can identify the primary next action on the home page and workspace center
- workspace hierarchy and return paths are explicit enough that users do not feel lost between overview, modules,
  documents, chat, tasks, and analytics
- the three scenario modules are easier to distinguish from their entry surfaces without renaming the products
- the user-facing public demo pages feel materially more presentable for external showcase use
- Stage E workbench behavior remains intact and understandable during the UX reset

## Next Step

Execute `tasks/stage-f-03-workspace-navigation-and-primary-flow-simplification.md` as the next Stage F task.

## First Task Wave

The first executable Stage F wave is:

- `tasks/archive/stage-f/stage-f-02-home-and-workspace-information-architecture-reset.md` (complete)
- `tasks/stage-f-03-workspace-navigation-and-primary-flow-simplification.md`
- `tasks/stage-f-04-module-positioning-and-entry-surface-clarification.md`
- `tasks/stage-f-05-demo-visual-system-and-showcase-polish.md`

This wave keeps Stage F focused on one bounded outcome: make the live public demo and workspace experience easier to
understand before the roadmap returns to deeper trust, eval, and capability expansion work.

## Completed So Far

The first Stage F task is now complete:

- `tasks/archive/stage-f/stage-f-02-home-and-workspace-information-architecture-reset.md`

It reduced first-contact overload on the home page and workspace center by splitting first-time entry from existing-work
continuation, moving demo limits behind lighter disclosure, and demoting deep workspace links that previously competed
with the primary start path.

## Relationship To The Long-Term Roadmap

The broader future direction remains in `docs/prd/LONG_TERM_ROADMAP.md`.

That document still holds:

- future AI capability waves such as MCP, richer orchestration, realtime interaction, and action-taking agents
- longer-horizon trust and eval flywheel depth
- later productization beyond the current workbench and UX reset baseline

Stage F is an inserted bounded stage that improves the user-facing surface before those later roadmap themes resume.
