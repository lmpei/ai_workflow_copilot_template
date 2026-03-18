# AGENTS

This file is the source of truth for AI coding agents working in this repository.

## Purpose

Use this document to understand how an agent should read the repo, plan work, change code, update docs, verify results,
and archive completed tasks.

## Read Order

When starting a task, read documents in this order:

1. `STATUS.md`
2. `CONTEXT.md`
3. `DECISIONS.md`
4. `ARCHITECTURE.md`
5. The active task in `tasks/`
6. Detailed docs in `docs/` as needed

## Working Model

The repository now uses a control-plane plus execution-layer workflow:

1. Discuss and narrow direction with a human.
2. Fix confirmed direction in text before coding.
3. Create or update a task in `tasks/`.
4. Implement only the scoped change.
5. Run relevant verification before handoff.
6. Update `STATUS.md`, `DECISIONS.md`, and related docs when the change is durable.
7. Archive completed tasks under `tasks/archive/`.

## Documentation Rules

Use the right file for the right kind of truth:

- `README.md`
  - Human entry point, quick start, common commands, and document navigation.
- `CONTEXT.md`
  - Stable project facts and boundaries.
- `STATUS.md`
  - Current phase, objective, blockers, active task, and next actions.
- `DECISIONS.md`
  - Confirmed decisions only; append new entries at the bottom.
- `ARCHITECTURE.md`
  - Stable architecture summary.
- `docs/`
  - Long-form docs and formal references.
- `tasks/`
  - Execution-ready task specs only.

Do not use `README.md` or archived tasks as the live source of current state.

## Repository Rules

- Keep FastAPI route handlers thin.
- Keep business logic in services.
- Keep persistence concerns in repositories.
- Reuse existing modules before inventing new abstractions.
- Treat `server/app/workers/` as live async entrypoints only.
- Frontend code should default to TypeScript.
- Do not present scaffold or draft surfaces as product-complete features.
- Do not rename the three module product names without human confirmation.
- Do not edit deployment or environment files unless the task explicitly requires it.
- Preserve the long-term value of `docs/` and `tasks/archive/`.

## Task Rules

- Every non-trivial code or doc change should map to a task file.
- Keep one primary active task whenever possible.
- Scope tasks so they can be verified in one pass.
- When a task completes, move it to `tasks/archive/` and update `STATUS.md`.

## Verification Baseline

Run the relevant checks for the changed surface.

Backend baseline:

- `cd server`
- `..\\.venv\\Scripts\\python.exe -m pytest tests`

Frontend baseline:

- `npm --prefix web run verify`

For docs-only tasks, perform a consistency review and update the control-plane docs together.

## Human Confirmation Required

Stop and confirm with a human before:

- changing product scope or phase direction
- changing module product names
- changing core architecture boundaries in a way that invalidates the docs of record
- changing environment, deployment, or destructive operational behavior
- deleting historical docs or task archives

## Output Expectations

At handoff, report:

1. modified files
2. what changed
3. verification run and result
4. blockers, risks, or follow-ups
