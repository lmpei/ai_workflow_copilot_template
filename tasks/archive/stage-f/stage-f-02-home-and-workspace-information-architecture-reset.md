# Task: stage-f-02-home-and-workspace-information-architecture-reset

## Goal

Reduce first-contact cognitive load on the home page and workspace center so users can tell what to do first without
reading through every platform surface at once.

## Project Stage

- Stage: Stage F
- Track: Delivery and Operations with Platform Reliability support

## Why

The live public demo works, but the home page and workspace center currently expose too much platform detail too early.
First-time users are asked to understand templates, limits, health, modules, workspaces, and deep links at the same
time instead of being shown one clear starting path.

## Context

Relevant documents:

- `docs/prd/STAGE_F_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `tasks/archive/stage-e/stage-e-09-public-demo-workbench-entry-and-walkthrough.md`
- `STATUS.md`

## Scope

Allowed work:

- simplify the information hierarchy of the home page and workspace center
- make the primary start path clearer for first-time users
- push secondary or operator-heavy information down, aside, or behind lighter disclosure
- keep the Stage E workbench continuation story visible without letting it dominate first contact

Disallowed work:

- broad workspace navigation redesign beyond the home page and workspace center
- module renaming
- backend feature expansion unrelated to front-end surface clarity

## Acceptance Criteria

- a first-time user can identify one primary next action on the home page
- the workspace center makes it obvious when to create a guided demo workspace versus when to continue existing work
- secondary platform details no longer compete equally with the primary entry path
- the public demo remains honest about its limits without overwhelming the user
