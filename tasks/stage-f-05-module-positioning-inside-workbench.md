# Task: stage-f-05-module-positioning-inside-workbench

## Goal

Clarify how Research Assistant, Support Copilot, and Job Assistant differ inside the new workspace workbench, without
relying on a separate module-explanation page and without renaming the products.

## Project Stage

- Stage: Stage F
- Track: Research and Delivery and Operations with Platform Reliability support

## Why

Once the workspace collapses into a single main workbench, module differences should appear inside that workbench
itself. Otherwise the project will still feel like three similar text-analysis tools that happen to share a shell.

## Context

Relevant documents:

- `docs/prd/STAGE_F_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `server/app/schemas/scenario.py`
- `tasks/stage-f-04-workspace-workbench-consolidation.md`
- `tasks/archive/stage-e/stage-e-02-support-case-workbench-foundation.md`
- `tasks/archive/stage-e/stage-e-03-job-hiring-workbench-foundation.md`
- `STATUS.md`

## Scope

Allowed work:

- clarify module-specific work objects, outputs, and best-fit use cases inside the unified workspace workbench
- make Support case and Job hiring-packet differences visible earlier than deep task or workbench history
- keep Research visibly different from Support and Job in the main user surface
- preserve current module product names

Disallowed work:

- renaming the three module products
- new backend module features as a substitute for clearer front-end explanation
- generic marketing copy that drifts away from the real system behavior

## Acceptance Criteria

- a first-time user can better distinguish the three modules from the workbench itself
- Support and Job workbench objects are explained earlier and more clearly
- Research remains visibly different from Support and Job on the user-facing surface
- the explanation stays grounded in the real platform contracts and persisted workbench behavior
