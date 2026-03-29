# Task: stage-f-04-workspace-workbench-consolidation

## Goal

Replace the current multi-page workspace model with one primary workspace workbench that can carry the main user path
without forcing users to hop across overview, modules, documents, chat, and tasks as peer-level destinations.

## Project Stage

- Stage: Stage F
- Track: Delivery and Operations with Platform Reliability and Research support

## Why

The current workspace still exposes too much platform structure. Even after the hierarchy reset, the product still asks
users to understand several separate pages before they can do real work. From the user's point of view, documents,
chat, and tasks belong to one continuous activity, while overview and modules do not justify their own top-level
pages.

## Context

Relevant documents:

- `docs/prd/STAGE_F_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `tasks/archive/stage-f/stage-f-02-home-and-workspace-information-architecture-reset.md`
- `tasks/archive/stage-f/stage-f-03-workspace-navigation-and-primary-flow-simplification.md`
- `tasks/archive/stage-e/stage-e-02-support-case-workbench-foundation.md`
- `tasks/archive/stage-e/stage-e-03-job-hiring-workbench-foundation.md`
- `STATUS.md`

## Scope

Allowed work:

- collapse the workspace's primary user path into one main workbench surface
- stop treating overview and modules as separate top-level destinations in the normal user journey
- make documents, chat, and tasks available from one primary workbench through selectable panels, drawers, or sections
- keep analytics accessible as a secondary review surface instead of a competing first-stop page
- preserve the real Support case and Job hiring-packet continuity introduced in Stage E

Disallowed work:

- module product renaming
- backend feature expansion as a substitute for front-end consolidation
- hidden deletion or reset of persisted workbench state
- broad visual-system polish beyond what is needed to make the single-workbench structure understandable

## Acceptance Criteria

- a user can enter a workspace and start from one obvious main workbench instead of choosing among several peer pages
- documents, chat, and tasks can be used from one primary surface
- overview and modules no longer compete as separate top-level pages in the core workspace flow
- analytics remains available without dominating the main path
- the resulting structure still tells the truth about real persisted Support cases and Job hiring packets
