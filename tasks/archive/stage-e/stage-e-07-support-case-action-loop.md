# Task: stage-e-07-support-case-action-loop

## Goal

Turn the Support case workbench from a readable history surface into a direct work surface where a user can continue a
case and move case state forward from the case itself.

## Project Stage

- Stage: Stage E
- Track: Platform Reliability with Research and Delivery and Operations support

## Why

`stage-e-02` introduced durable Support cases and timeline history, but day-to-day follow-up still starts from task
memory rather than from the case workbench object.

## Context

Relevant documents:

- `docs/prd/STAGE_E_PLAN.md`
- `tasks/archive/stage-e/stage-e-02-support-case-workbench-foundation.md`
- `tasks/archive/stage-c/stage-c-12-support-escalation-and-follow-up-workflow.md`
- `tasks/archive/stage-e/stage-e-04-public-demo-workbench-continuity.md`
- `STATUS.md`

## Scope

Allowed work:

- let a user start the next Support follow-up from an existing case workbench entry
- make bounded case-status progression explicit at the case surface
- keep escalation packet continuity readable when a case is continued
- preserve the shared task runtime instead of bypassing it

Disallowed work:

- broad ticketing-suite ambition
- SLA automation or routing systems
- unrelated Job or Research workbench implementation

## Acceptance Criteria

- a user can continue a Support case directly from the case workbench surface
- case-level status progression is clearer than raw task-history inspection
- case follow-up remains grounded in the shared task runtime rather than a shadow execution path
- the live public demo can explain the Support action loop without hidden operator steps
