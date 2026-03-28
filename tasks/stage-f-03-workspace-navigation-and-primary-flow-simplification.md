# Task: stage-f-03-workspace-navigation-and-primary-flow-simplification

## Goal

Make the workspace feel like a navigable product hierarchy instead of a flat list of equal tools.

## Project Stage

- Stage: Stage F
- Track: Delivery and Operations with Platform Reliability support

## Why

Once a user enters a workspace, the current surface makes overview, modules, documents, chat, tasks, and analytics all
look equally primary. This creates navigation ambiguity, unclear return paths, and too much page-switching for the
main workflow.

## Context

Relevant documents:

- `docs/prd/STAGE_F_PLAN.md`
- `tasks/stage-f-02-home-and-workspace-information-architecture-reset.md`
- `docs/development/PUBLIC_DEMO_SHOWCASE_PATH.md`
- `STATUS.md`

## Scope

Allowed work:

- clarify workspace-level hierarchy and return paths
- make the main workflow easier to follow across documents, chat, and tasks
- demote secondary surfaces that should not compete equally with the main workflow
- preserve access to analytics and deeper platform surfaces without forcing them into the main path

Disallowed work:

- broad module-positioning rewrite beyond workspace hierarchy
- hidden deletion or reset of persisted workbench state
- unrelated backend execution changes

## Acceptance Criteria

- users can tell where they are inside a workspace
- users can return to the previous level without guessing
- the main workflow is easier to follow than the current flat page model
- analytics and other advanced surfaces no longer dominate the primary workspace path
