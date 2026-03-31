# Task: stage-f-09-chat-first-workbench-shell

## Goal

Reshape the workspace workbench so chat becomes the primary interaction surface and documents plus task actions become
secondary, object-aware affordances.

## Project Stage

- Stage: Stage F
- Track: Delivery and Operations with Research and Platform Reliability support

## Why

The current single-workbench model is better than the old multi-page model, but it still feels too panel-driven. The
human clarified that the product should feel closer to one object-aware, chat-centered workspace rather than a set of
peer panels for documents, chat, and tasks.

## Context

Relevant documents:

- `docs/prd/STAGE_F_PLAN.md`
- `tasks/stage-f-08-project-home-workspace-center-reset.md`
- `ARCHITECTURE.md`

## Scope

Allowed work:

- make chat the primary visual and interaction center of the workspace
- keep one compact object summary in view
- reduce documents to lightweight upload and lookup affordances
- reduce tasks to quick actions and execution feedback instead of a peer panel

Disallowed work:

- hiding real task execution state entirely
- backend workflow changes unrelated to front-end workbench structure
- renaming the three module products

## Acceptance Criteria

- the workspace reads as one chat-first workbench instead of as three equal panels
- documents are available without dominating the screen
- task execution can still be triggered and understood without appearing as a full peer page or full peer panel
- the workbench remains honest about the current object and current state
