# Task: stage-f-04-module-positioning-and-entry-surface-clarification

## Goal

Make the three scenario modules easier to understand from their entry surfaces without renaming the module products.

## Project Stage

- Stage: Stage F
- Track: Research and Delivery and Operations with Platform Reliability support

## Why

From a first-time user perspective, Research Assistant, Support Copilot, and Job Assistant currently look too similar.
The real differences in work objects and outputs appear too late, so the front-end does not help users choose the right
module with confidence.

## Context

Relevant documents:

- `docs/prd/STAGE_F_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `server/app/schemas/scenario.py`
- `tasks/archive/stage-e/stage-e-02-support-case-workbench-foundation.md`
- `tasks/archive/stage-e/stage-e-03-job-hiring-workbench-foundation.md`
- `STATUS.md`

## Scope

Allowed work:

- clarify module-specific work objects, outputs, and best-fit use cases on entry surfaces
- make Support case and Job hiring-packet differences visible earlier in the journey
- reduce the impression that all three modules are generic text-analysis tools
- preserve current module product names

Disallowed work:

- renaming the three module products
- new module-backend feature expansion as a substitute for clearer front-end explanation
- generic marketing copy that drifts away from the real system behavior

## Acceptance Criteria

- a first-time user can better distinguish the three modules before entering deep task or workbench flows
- Support and Job workbench objects are explained earlier and more clearly
- Research remains visibly different from Support and Job on the user-facing surface
- the front-end explanation stays grounded in the real platform contracts
