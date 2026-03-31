# Stage F Plan

## Stage Name

`Stage F: Public Demo Experience Clarification and UX Reset`

## Status

- Status: active
- Opened At: 2026-03-28
- First Task Wave: complete
- Second Task Wave: complete
- Third Task Wave: complete
- Narrow Post-Wave Follow-Up: complete`r`n- Final Reset Follow-Up: complete

## Position In The Project

Stage F begins after the closeout of Stage E. Stage E proved that the platform can persist Support cases and Job
hiring packets as real workbench objects, and that the public demo can explain when to start from a fresh guided
workspace versus when to continue from an existing workbench object. The first Stage F wave then reduced overload,
collapsed the workspace into one primary workbench, and clarified the three modules from inside that workbench.

The second Stage F wave then finished the next structural layer: separate the root site from the product, move the
project onto its own clearer home route, turn the workbench into a more chat-first surface, turn the rest of the
workspace into summonable supporting surfaces, and finally add one bounded visual-polish pass to the highest-traffic
pages. Human review then clarified that the direction was right but the current surface was still too verbose, too
single-column, and too visibly panelized. Stage F therefore continues with a third bounded follow-up wave instead of
closing.

## Planning Model

Stage F continues to operate under the same three-track roadmap model:

1. `Research`
2. `Platform Reliability`
3. `Delivery and Operations`

The tracks remain parallel, but Stage F shifts the emphasis again. Delivery and Operations becomes the primary track
because the main goal is to make the public-facing and project-facing experience easier to understand without hiding
real platform behavior.

## Priority Model

- Primary track:
  - `Delivery and Operations` as the user-facing surface and demo-experience reset layer
- Required parallel tracks:
  - `Platform Reliability` to keep persistent workbench state honest and visible during the UX reset
  - `Research` as the reference workflow when the front-end needs to explain why the three modules are different

Stage F should not optimize for new AI capability waves if those waves delay the information-architecture reset or
increase first-time user confusion.

## Stage Goal

Turn the public demo into a clearer product shape by:

- separating the root personal homepage from the logged-in project home
- reshaping the project home into a lighter workspace center
- turning the workspace into a more chat-first, object-aware workbench
- turning documents, actions, execution detail, and analytics into summonable supporting surfaces
- adding one bounded visual-system polish pass after the structure lands

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

Reduce first-time user confusion and make the live public demo easier to understand, navigate, and present, even after
the second-wave structural reset.

### Focus Areas

- personal homepage versus project-home separation
- project-home workspace center with one lightweight guided-demo entry and one bounded existing-work list
- chat-first workbench structure where documents and task actions become supporting surfaces rather than peer pages
- analytics and deeper inspection as summonable secondary surfaces instead of constant page-level destinations
- visual polish on the highest-traffic surfaces after the new structure lands
- one viewport-first project home where primary information and actions fit without needless scrolling
- one conversation-first workbench where document upload, context access, and task execution no longer read like visible peer panels

### Expected Outcomes

- the root site behaves like a personal homepage instead of a workspace center
- the project-facing home behaves like a product entry surface instead of a duplicate homepage
- the workspace feels more like one object-aware workbench and less like a tool console
- the public demo looks intentional enough for external showcase use
- the user does not need repeated abstract explanation to understand where to start

## Non-Goals

Stage F does not primarily optimize for:

- renaming the three scenario modules
- new MCP, realtime, or computer-use capability waves
- deeper Support or Job backend workbench expansion beyond the Stage E baseline
- production-grade multi-tenant SaaS polish
- hidden simplification that conceals real continuity, demo limits, or operator boundaries
- a destructive rewrite that throws away the existing backend, auth flow, or workbench-object behavior

## Execution Rules

- Stage F tasks should use `stage-f-*` naming
- solve structure before solving visual polish
- do not hide important state behind misleading simplification
- keep the live public demo honest about what is demo-grade versus durable
- prefer fewer, clearer entry points over exposing every platform surface at once
- preserve working data and runtime flows even if the current front-end surface needs selective rewrites

## Success Criteria

Stage F is successful when:

- the root public site behaves like a personal homepage rather than a product workspace entry
- the project-facing home behaves like one denser product home / workspace center instead of repeating the root homepage
- existing workspaces no longer expand the page without bound and instead live in one fixed-height continuation region
- the workspace itself feels chat-first, with documents, task actions, execution detail, and analytics available on
  demand instead of competing as peer pages or equal-weight panels
- the three scenario modules remain easier to distinguish from inside the workbench without renaming the products
- Stage E workbench behavior remains intact and understandable during the UX reset
- the main product surfaces can explain themselves within one viewport and one obvious path instead of depending on long explanatory stacks

## Next Step

Review the full Stage F result, then decide whether the stage should close cleanly or whether any later front-end work
belongs in a new planning unit instead of more Stage F extension.

## First Task Wave

The first executable Stage F wave is:

- `tasks/archive/stage-f/stage-f-02-home-and-workspace-information-architecture-reset.md` (complete)
- `tasks/archive/stage-f/stage-f-03-workspace-navigation-and-primary-flow-simplification.md` (complete)
- `tasks/archive/stage-f/stage-f-04-workspace-workbench-consolidation.md` (complete)
- `tasks/archive/stage-f/stage-f-05-module-positioning-inside-workbench.md` (complete)
- `tasks/archive/stage-f/stage-f-06-demo-visual-system-and-showcase-polish-superseded.md` (superseded before execution)

This wave kept Stage F focused on one bounded outcome: make the live public demo and workspace experience easier to
understand before the roadmap returned to deeper trust, eval, and capability expansion work. Its originally planned
visual-polish-only final step was later superseded by a second wave that changed the site and workbench structure more
deeply before visual polish resumed.

## Completed So Far

The first four Stage F tasks are now complete:

- `tasks/archive/stage-f/stage-f-02-home-and-workspace-information-architecture-reset.md`
- `tasks/archive/stage-f/stage-f-03-workspace-navigation-and-primary-flow-simplification.md`
- `tasks/archive/stage-f/stage-f-04-workspace-workbench-consolidation.md`
- `tasks/archive/stage-f/stage-f-05-module-positioning-inside-workbench.md`

They reduced first-contact overload on the home page and workspace center, then added one explicit workspace
hierarchy with breadcrumb navigation and grouped surfaces, and then collapsed the remaining multi-page workspace model
into one primary workbench. That workbench now also explains module differences through real work objects and
continuity rules.

## Second Task Wave

The second executable Stage F wave is:

- `tasks/archive/stage-f/stage-f-07-personal-homepage-and-project-entry-split.md` (complete)
- `tasks/archive/stage-f/stage-f-08-project-home-workspace-center-reset.md` (complete)
- `tasks/archive/stage-f/stage-f-09-chat-first-workbench-shell.md` (complete)
- `tasks/archive/stage-f/stage-f-10-supporting-panels-and-analytics-drawer.md` (complete)
- `tasks/archive/stage-f/stage-f-11-showcase-visual-polish.md` (complete)

This wave accepted the human clarification that the product should no longer behave like a root-level demo console. The
site first became a personal homepage plus project directory, then the project itself became a lighter workspace
center, then the primary workspace became chat-first, then the supporting detail became summonable, and finally the
highest-traffic surfaces received one bounded visual-polish pass.

The second wave is now complete, but it is no longer treated as the Stage F endpoint. Human review confirmed that one
more tightly bounded follow-up is justified before Stage F can close.

## Third Task Wave

The third executable Stage F wave is:

- `tasks/archive/stage-f/stage-f-13-personal-homepage-and-project-home-viewport-reset.md` (complete)
- `tasks/archive/stage-f/stage-f-14-conversation-first-workbench-rebuild.md` (complete)
- `tasks/archive/stage-f/stage-f-15-summoned-supporting-surfaces-and-operator-affordances.md` (complete)
- `tasks/archive/stage-f/stage-f-16-showcase-visual-redesign-and-legacy-cleanup.md` (complete)

This wave accepts the human clarification that the current front-end still feels too verbose and too panelized. The
goal is not another small polish pass. The goal is to finish the product-shape reset: the root site should act like a
true personal homepage, the project-facing home should fit the primary story and actions inside one denser viewport,
the main workspace should center on one conversation surface, and the remaining detail should only appear when the
user asks for it.

The whole wave is now complete. The root personal homepage and the `/app` project home are denser and more
viewport-first than the second-wave versions, the workspace itself now centers on one conversation-first surface
instead of a visible set of peer panels, supporting detail now behaves like summoned secondary surfaces, and the final
cleanup and visual redesign pass has landed. The remaining question is no longer implementation scope, but whether
Stage F should now close or whether a later tiny cleanup deserves its own planning unit.

## Relationship To The Long-Term Roadmap

The broader future direction remains in `docs/prd/LONG_TERM_ROADMAP.md`.

That document still holds:

- future AI capability waves such as MCP, richer orchestration, realtime interaction, and action-taking agents
- longer-horizon trust and eval flywheel depth
- later productization beyond the current workbench and UX reset baseline

Stage F is an inserted bounded stage that improves the user-facing surface before those later roadmap themes resume.

## Narrow Post-Wave Follow-Up

The current narrow follow-up is:

- `tasks/archive/stage-f/stage-f-17-workbench-density-and-direct-affordances.md` (complete)

This follow-up does not reopen the Stage F structure reset. It only addresses the last narrow usability gaps confirmed by
human review after the third wave: too much vertical space at the top of the main conversation surface, repeated
explanation that no longer adds action value, and a document-upload affordance that should support drag-and-drop as
well as click-to-select while keeping an explicit upload button.

The follow-up is now complete. The workbench top area is denser, repeated explanatory surfaces have been reduced, and the
document entry surface now supports both drag-and-drop and click-to-select while keeping the explicit upload button. The
remaining Stage F question is now stage closeout, not another active implementation gap.


## Final Reset Follow-Up

The final Stage F reset follow-up is:

- `tasks/archive/stage-f/stage-f-18-project-home-and-research-workflow-reset.md` (complete)

This follow-up accepts one last human clarification: the project-facing home still needed to behave less like a
workspace-center explanation page, and the main workbench still needed to read less like a generic chat surface and more
like a research workflow page. The result is a denser /app home with login or session actions at the top, one
lightweight guided-demo row, one manual-create surface, and one bounded existing-work region, plus a clearer main
workspace where prompt chips are visibly clickable, 开始分析 is the primary CTA, analysis progress stays in the main
column, and the right rail behaves like a state-oriented research panel.
