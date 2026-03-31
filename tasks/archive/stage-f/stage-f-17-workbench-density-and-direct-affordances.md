# Task: Stage F Workbench Density And Direct Affordances

## Goal

Apply one narrow post-wave follow-up that removes repeated explanation from the workbench, reduces wasted vertical space,
adds direct drag-and-drop document upload, and renames abstract action labels into clearer result-oriented affordances.

## Project Phase

- Phase: Phase 5 follow-up
- Scenario module: cross-module

## Why

Human review after the third Stage F wave confirmed that the overall direction is now right, but the workbench still has
three specific product-shape issues: the top of the conversation surface is too tall, some visible cards repeat the
same information, and the document entry surface is still too weak for day-to-day use. These are no longer broad
structure questions; they are one narrow density and direct-affordance pass.

## Context

Relevant surfaces:

- `web/components/workspace/workspace-workbench-panel.tsx`
- `web/components/chat/chat-panel.tsx`
- `web/components/documents/document-manager.tsx`
- any tiny supporting text or labels that still read as abstract explanation rather than concrete actions

## Flow Alignment

- Flow A / B / C / D:
  - tighten the main user path after the conversation-first model is already in place
- Related APIs:
  - existing chat and document APIs only
- Related schema or storage changes:
  - none

## Dependencies

- Prior task:
  - `tasks/archive/stage-f/stage-f-16-showcase-visual-redesign-and-legacy-cleanup.md`
- Blockers:
  - none

## Scope

Allowed files:

- `web/components/workspace/**`
- `web/components/chat/**`
- `web/components/documents/**`
- related control-plane docs and this task file

Disallowed files:

- backend runtime or schema changes
- deployment/env files
- broad new layout rewrites outside the already-confirmed workbench surfaces

## Deliverables

- Code changes:
  - compress the visible workbench header and chat empty state
  - remove repeated explanatory cards where they do not add action value
  - make the document entry surface support drag-and-drop plus click-to-select while keeping the upload button
  - rename abstract action labels into result-oriented labels where needed
- Test changes:
  - none required unless contracts change
- Docs changes:
  - update Stage F control-plane docs if the follow-up lands durably

## Acceptance Criteria

- the main workbench header no longer wastes large vertical space
- the visible workbench surface no longer repeats the same “what this is” explanation in multiple places
- the current-focus surface is either reduced to actionable state or removed where redundant
- document upload supports both dragging a file in and clicking to choose a file, while keeping an explicit upload button
- result-oriented action labels are clearer than abstract labels like generic “actions” wording

## Verification Commands

- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - a user can enter a workspace and immediately focus on the main conversation path
- Edge case:
  - dragging or selecting a file still results in the same upload pipeline
- Error case:
  - no broken imports or type errors after the density cleanup

## Risks

- over-compressing the workbench until key continuity signals disappear
- making the upload affordance look better but behave less predictably

## Rollback Plan

- revert the narrow follow-up commit or the affected workbench files only
