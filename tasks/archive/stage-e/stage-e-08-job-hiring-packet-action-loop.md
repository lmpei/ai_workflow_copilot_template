# Task: stage-e-08-job-hiring-packet-action-loop

## Goal

Turn the Job hiring packet workbench from a readable packet history into a direct work surface where shortlist refresh,
candidate comparison, and hiring notes can start from the packet itself.

## Project Stage

- Stage: Stage E
- Track: Platform Reliability with Research and Delivery and Operations support

## Why

`stage-e-03` introduced durable Job hiring packets and timeline history, but the next round of hiring work still starts
from task memory instead of from the packet workbench object.

## Context

Relevant documents:

- `docs/prd/STAGE_E_PLAN.md`
- `tasks/archive/stage-e/stage-e-03-job-hiring-workbench-foundation.md`
- `tasks/archive/stage-c/stage-c-13-job-shortlist-and-candidate-comparison.md`
- `tasks/archive/stage-e/stage-e-04-public-demo-workbench-continuity.md`
- `STATUS.md`

## Scope

Allowed work:

- let a user start shortlist refresh or comparison work from an existing hiring packet
- make packet-level decision notes or review notes readable at the packet surface
- preserve candidate-pool continuity without bypassing the shared task runtime
- keep the live public demo able to explain what changed between packet revisions

Disallowed work:

- broad ATS ambition
- external recruiting integrations
- unrelated Support or Research workbench implementation

## Acceptance Criteria

- a user can continue Job hiring work directly from a hiring packet
- shortlist refresh and comparison history become easier to understand from the packet itself
- packet-level notes remain bounded and demo-usable
- the live public demo can show the Job action loop without depending on raw task memory
