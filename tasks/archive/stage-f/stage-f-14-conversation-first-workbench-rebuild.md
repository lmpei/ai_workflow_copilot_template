# Task: Stage F Conversation-First Workbench Rebuild

## Goal

Rebuild the main workspace so it behaves like one conversation-first product surface instead of a visible set of peer
panels.

## Project Phase

- Phase: Phase 5 follow-up
- Scenario module: cross-module

## Why

The current workbench direction is correct, but documents, task work, and analytics still read too much like visible
regions. The human explicitly clarified that the main workspace should feel closer to one conversation surface where
document and task controls are lightweight affordances.

## Context

Relevant surfaces:

- `web/components/workspace/workspace-workbench-panel.tsx`
- `web/components/chat/chat-panel.tsx`
- `web/components/documents/document-manager.tsx`
- module action panels under `web/components/`

## Flow Alignment

- Flow A / B / C / D:
  - open workspace -> understand current object -> continue work through the main conversation surface
- Related APIs:
  - existing chat, document, task, Support case, and Job hiring-packet APIs
- Related schema or storage changes:
  - none expected

## Dependencies

- Prior task:
  - `tasks/archive/stage-f/stage-f-13-personal-homepage-and-project-home-viewport-reset.md`
- Blockers:
  - none

## Scope

Allowed files:

- `web/components/workspace/*`
- `web/components/chat/*`
- `web/components/documents/*`
- `web/components/research/*`
- `web/components/support/*`
- `web/components/job/*`
- `web/lib/navigation.ts`
- related control-plane docs

Disallowed files:

- backend API contracts unless a bug forces a minimal compatible fix
- deployment/env files

## Deliverables

- Code changes:
  - one clearer conversation-first workspace shell
  - document upload/context access as lightweight controls
  - task work exposed as action buttons instead of visible peer panels
- Test changes:
  - frontend coverage only if component contracts change
- Docs changes:
  - Stage F control-plane updates

## Acceptance Criteria

- the workspace has one obvious center
- document handling feels like a supporting affordance rather than a page-sized region
- task work feels like action-taking rather than a separate destination
- Support case and Job hiring-packet continuity remain visible and intact

## Verification Commands

- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - a user can upload context, chat, and trigger the next action without switching mental models
- Edge case:
  - Research still works as the deepest document-heavy reference flow
- Error case:
  - no fake hiding of real state, active actions, or continuity objects

## Risks

- turning the workspace into a pure chat clone and losing workbench-object depth
- hiding important execution state too aggressively

## Rollback Plan

- revert the workbench-related front-end files only
