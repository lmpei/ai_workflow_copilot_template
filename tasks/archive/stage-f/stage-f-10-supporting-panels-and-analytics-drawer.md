# Task: stage-f-10-supporting-panels-and-analytics-drawer

## Goal

Turn documents, execution detail, and analytics into summonable supporting surfaces that help the main workbench
without competing with it.

## Project Stage

- Stage: Stage F
- Track: Delivery and Operations with Research and Platform Reliability support

## Why

Once chat becomes the primary workbench surface, the rest of the interface should support that focus instead of
pulling the user into more permanent page destinations. The human explicitly asked for analytics to be available by
button rather than as a constant presence.

## Context

Relevant documents:

- `docs/prd/STAGE_F_PLAN.md`
- `tasks/stage-f-09-chat-first-workbench-shell.md`
- `ARCHITECTURE.md`

## Scope

Allowed work:

- document drawer, document picker, or equivalent lightweight supporting surface
- execution-status and recent-action visibility that supports the main workbench
- analytics opened by button, drawer, or modal instead of as a constant first-stop page
- module-specific supporting surfaces that reinforce object continuity

Disallowed work:

- reintroducing the old multi-page model
- deep observability or backend analytics changes

## Acceptance Criteria

- documents, execution detail, and analytics are all reachable on demand
- those surfaces no longer dominate the default workspace view
- the main workbench stays focused while still exposing the supporting detail needed for real work and honest demos
