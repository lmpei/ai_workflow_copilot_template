# Task: stage-e-04-public-demo-workbench-continuity

## Goal

Keep the live public demo usable and honest while Stage E introduces Support and Job persistent workbench layers.

## Project Stage

- Stage: Stage E
- Track: Delivery and Operations with Platform Reliability support

## Why

After Stage D, the project now has a real public demo. Stage E will add deeper persistent state, so the operator needs a
bounded continuity and refresh story before that new state starts accumulating.

## Context

Relevant documents:

- `docs/prd/STAGE_E_PLAN.md`
- `docs/development/PUBLIC_DEMO_OPERATOR_RUNBOOK.md`
- `docs/development/PUBLIC_DEMO_ROLLOUT_EVIDENCE_2026-03-27.md`
- `docs/development/PUBLIC_DEPLOYMENT_PATH.md`
- `STATUS.md`

## Scope

Allowed work:

- extend public-demo refresh and smoke guidance for new workbench state
- clarify which workbench objects may be preserved versus reset between demos
- keep the live public-demo story honest for interviews and outside viewers

Disallowed work:

- full production operations hardening
- unrelated module-depth work
- new hosting-target redesign

## Acceptance Criteria

- the live demo has one bounded continuity story after workbench state lands
- refresh and smoke guidance explicitly covers new Support and Job persistent objects
- future demos do not rely on hidden manual cleanup or vague operator memory