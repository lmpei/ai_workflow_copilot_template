# Task: stage-e-09-public-demo-workbench-entry-and-walkthrough

## Goal

Keep the public demo understandable after Stage E makes Support and Job workbench objects actionable instead of merely
persistent.

## Project Stage

- Stage: Stage E
- Track: Delivery and Operations with Platform Reliability support

## Why

Once Support cases and Job hiring packets become direct work surfaces, the public demo needs one bounded walkthrough
story that shows where a new viewer should start and how existing workbench state should be explained honestly.

## Context

Relevant documents:

- `docs/prd/STAGE_E_PLAN.md`
- `docs/development/PUBLIC_DEMO_WORKBENCH_CONTINUITY.md`
- `tasks/archive/stage-e/stage-e-04-public-demo-workbench-continuity.md`
- `STATUS.md`

## Scope

Allowed work:

- clarify where workbench-first entry should appear in the live public demo
- keep Support and Job walkthroughs honest once direct case / packet actions exist
- extend the operator-facing demo story only as much as needed for bounded Stage E workbench actions

Disallowed work:

- new hosting-target redesign
- production-grade operations hardening
- unrelated module-depth work outside Support and Job workbench actions

## Acceptance Criteria

- the live public demo has one bounded walkthrough story for workbench-first Support and Job actions
- outside viewers do not need hidden operator explanation to understand whether they should start from a fresh workspace,
  an existing case, or an existing hiring packet
- Stage E remains demo-grade and bounded rather than drifting into broad operational redesign
