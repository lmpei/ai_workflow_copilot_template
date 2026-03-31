# Task: Stage F Project Home And Research Workflow Reset

## Goal

Rebuild the `/app` project-facing home into a denser project start surface, then reshape the main workspace from a
generic conversation page into a clearer research-workflow surface that still preserves existing document, analytics,
trace, and formal-output capabilities.

## Project Phase

- Phase: Phase 5 follow-up
- Scenario module: cross-module with Research as the reference workflow

## Why

Human review after `stage-f-17` confirmed that the remaining gaps were no longer small density or wording issues. The
`/app` entry surface still repeated too much explanation, the existing-work region still behaved too much like a card
list instead of a quick continuation area, and the main workbench still read like a generic chat surface instead of a
page that helps a user complete a full research flow.

## Context

Relevant surfaces:

- `web/app/app/page.tsx`
- `web/app/page.tsx`
- `web/components/workspace/workspace-center-panel.tsx`
- `web/components/workspace/workspace-workbench-panel.tsx`
- `web/components/chat/chat-panel.tsx`
- `web/components/documents/document-manager.tsx`

## Flow Alignment

- Flow A / B / C / D:
  - reshape the project-facing start page and the primary workspace around one clearer research-oriented path
- Related APIs:
  - existing workspace, document, chat, metrics, trace, and task APIs only
- Related schema or storage changes:
  - none

## Dependencies

- Prior task:
  - `tasks/archive/stage-f/stage-f-17-workbench-density-and-direct-affordances.md`
- Blockers:
  - none

## Scope

Allowed files:

- `web/app/**`
- `web/components/workspace/**`
- `web/components/chat/**`
- `web/components/documents/**`
- related control-plane docs and this task file

Disallowed files:

- backend runtime or schema changes
- deployment/env files
- module product renaming
- destructive cleanup of historical docs or archives

## Deliverables

- Code changes:
  - rebuild `/app` into a denser project home with one lightweight guided-demo row, one manual-create surface, and one
    bounded existing-work region
  - remove repeated project-home explanation and move login/register entry into the top project surface
  - make existing workspaces lighter, fully clickable continuation cards without per-card CTA buttons
  - rebuild the main workspace so the left side reads as one research workflow:
    - clickable prompt chips
    - editable prompt insertion
    - one primary `开始分析` CTA
    - main analysis / reply flow in the center
  - rebuild the right side into a research-state sidebar:
    - runtime status
    - document status and upload entry
    - analytics / trace / readiness entry
    - formal output entry
  - keep analytics, trace, documents, and formal outputs available without exposing them as peer pages
- Test changes:
  - none required unless contracts change
- Docs changes:
  - update Stage F control-plane docs if this reset lands durably

## Acceptance Criteria

- `/app` no longer feels like a duplicated workspace-center explanation page
- the top of `/app` includes the project title, a short project description, and clear login/register or session actions
- the guided-demo entry is lightweight and one-row
- the existing-work region is bounded, lighter, and uses fully clickable cards with hover feedback instead of per-card
  open buttons
- the main workspace reads as a research workflow surface rather than a generic explanatory chat page
- prompt chips look obviously clickable and insert text into the input area when selected
- the primary CTA is `开始分析` and is visually stronger than secondary controls
- analysis progress and results stay in the main column instead of being displaced into the right rail
- the right rail behaves like a research state panel instead of a loose collection of unrelated buttons
- terms like `grounded` are no longer exposed to users in untranslated form

## Verification Commands

- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - a user can enter `/app`, understand the primary actions quickly, and continue or create work without scanning long
    explanatory text
- Edge case:
  - clicking a prompt chip inserts editable text into the main input without immediately sending the request
- Error case:
  - no broken imports or type errors after the layout and workbench reset

## Risks

- rebuilding the main workspace too aggressively and temporarily weakening non-Research module continuity
- accidentally hiding analytics or formal-output entry too deeply while simplifying the visible layout

## Rollback Plan

- revert the `stage-f-18` commit or the affected project-home / workbench files only
