# Task: Stage F Wave Three Replanning

## Goal

Fix the remaining Stage F product-shape problems in text before more front-end code changes happen.

## Project Phase

- Phase: Phase 5 follow-up
- Scenario module: cross-module

## Why

The first two Stage F waves improved the structure, but human review confirmed that the current front-end still feels
too verbose, too single-column, and too visibly panelized. The repo needs one more bounded planning pass before more
implementation work starts.

## Context

Relevant docs:

- `STATUS.md`
- `CONTEXT.md`
- `DECISIONS.md`
- `docs/prd/STAGE_F_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`

## Flow Alignment

- Delivery and Operations:
  - project-facing surface reset
  - chat-first workbench rearchitecture
- Platform Reliability:
  - preserve Support case and Job hiring-packet continuity during UI change
- Research:
  - keep Research as the reference workflow when module differences still need to stay legible

## Dependencies

- Prior task:
  - `tasks/archive/stage-f/stage-f-11-showcase-visual-polish.md`
- Blockers:
  - none

## Scope

Allowed files:

- `STATUS.md`
- `CONTEXT.md`
- `DECISIONS.md`
- `docs/prd/STAGE_F_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `tasks/`

Disallowed files:

- `server/`
- `web/`
- deployment or environment files

## Deliverables

- Code changes:
  - none
- Test changes:
  - none
- Docs changes:
  - redefine the remaining Stage F work as a third bounded wave
  - create the next executable task stack

## Acceptance Criteria

- the control-plane docs agree that Stage F remains open
- the new task stack reflects the confirmed product direction
- the repo has one new primary active task

## Verification Commands

- Docs:
  - `git diff --check`

## Tests

- Normal case:
  - Stage F can continue without ambiguity
- Edge case:
  - previous completed Stage F waves remain preserved as history
- Error case:
  - avoid reopening broad unscoped UI churn

## Risks

- planning too broadly and losing bounded execution
- treating a front-end reset like a destructive full rewrite of the repo

## Rollback Plan

- revert the control-plane doc changes and task files only
