# Task: stage-e-03-job-hiring-workbench-foundation

## Goal

Introduce the first persistent Job hiring workbench layer so candidate comparison and shortlist work are preserved as a
reusable hiring object rather than only as isolated task outputs.

## Project Stage

- Stage: Stage E
- Track: Platform Reliability with Research and Delivery and Operations support

## Why

Stage C proved that Job Assistant can perform structured candidate review and shortlist comparison, but the module still
ends at task outputs rather than a durable hiring workbench.

## Context

Relevant documents:

- `docs/prd/STAGE_E_PLAN.md`
- `docs/prd/LONG_TERM_ROADMAP.md`
- `tasks/archive/stage-c/stage-c-03-job-assistant-structured-hiring-workflow.md`
- `tasks/archive/stage-c/stage-c-13-job-shortlist-and-candidate-comparison.md`
- `STATUS.md`

## Scope

Allowed work:

- define one persistent Job hiring packet or shortlist object
- preserve candidate-set membership, comparison history, and next-step notes in that workbench object
- surface the workbench through the Job UI without bypassing the shared task runtime
- keep demo-ready continuity and reset expectations explicit

Disallowed work:

- broad ATS ambition
- unrelated Support or Research workbench implementation
- external recruiting integrations

## Acceptance Criteria

- Job has one persistent workbench object with durable identity
- candidate comparison and shortlist history can be inspected through that object
- the UI exposes a usable hiring workbench surface for demo and review
- the public demo remains operable with bounded continuity expectations