# Task: stage-e-02-support-case-workbench-foundation

## Goal

Introduce the first persistent Support case workbench layer so Support collaboration no longer depends only on completed
task history.

## Project Stage

- Stage: Stage E
- Track: Platform Reliability with Research and Delivery and Operations support

## Why

Stage C proved that Support can handle structured grounded case workflows and follow-up chains, but the module still
stores most durable collaboration value in task outputs instead of in a case workbench.

## Context

Relevant documents:

- `docs/prd/STAGE_E_PLAN.md`
- `docs/prd/LONG_TERM_ROADMAP.md`
- `docs/prd/STAGE_D_PLAN.md`
- `tasks/archive/stage-c/stage-c-02-support-copilot-grounded-case-workflow.md`
- `tasks/archive/stage-c/stage-c-12-support-escalation-and-follow-up-workflow.md`
- `STATUS.md`

## Scope

Allowed work:

- define one persistent Support case object and response shape
- relate completed Support tasks and follow-up chains to that case object
- add bounded case timeline, status, and escalation continuity
- surface the case workbench in the Support UI without replacing the shared task runtime

Disallowed work:

- broad CRM or ticketing-suite ambition
- unrelated Job or Research workbench implementation
- production-grade case routing or SLA automation

## Acceptance Criteria

- Support has one persistent case workbench object with durable identity
- follow-up and escalation flows can be read through the case workbench rather than only through task history
- the UI exposes the new case surface clearly enough for demo use
- the live public demo remains honest about any reset or continuity limits
