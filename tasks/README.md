# Tasks

This directory holds execution-ready task specs.

## Purpose

Use `tasks/` for scoped work that is ready to execute. Use `tasks/archive/` for completed work. Use `STATUS.md` for the
current state of the project.

## Rules

- Keep active tasks in `tasks/`.
- Move completed tasks to `tasks/archive/`.
- Prefer one primary active task at a time.
- Update `STATUS.md` to point at the current active task.
- Add durable project choices to `DECISIONS.md` when they become confirmed.

## Naming

- Keep archived phase tasks in their original naming scheme.
- Historical Phase 5 task specs live under `tasks/archive/phase5/`.
- Use `stage-a-*` naming for Stage A work.
- Archive completed Stage A tasks under `tasks/archive/stage-a/`.
- Use `stage-b-*` naming for Stage B work.
- Archive completed Stage B tasks under `tasks/archive/stage-b/`.
- Use `stage-c-*` naming for Stage C work.
- Archive completed Stage C tasks under `tasks/archive/stage-c/`.
- Use `stage-d-*` naming for Stage D work.
- Archive completed Stage D tasks under `tasks/archive/stage-d/`.
- Use `stage-e-*` naming for Stage E work.
- Archive completed Stage E tasks under `tasks/archive/stage-e/`.
- Use `stage-f-*` naming for Stage F work.
- Archive completed Stage F tasks under `tasks/archive/stage-f/`.
- Use `stage-g-*` naming for Stage G work.
- Archive completed Stage G tasks under `tasks/archive/stage-g/`.
- Use `stage-h-*` naming for Stage H work.
- Archive completed Stage H tasks under `tasks/archive/stage-h/`.
- If the planning model changes again in a later stage, record that choice in `DECISIONS.md` before changing naming.

## Relationship to Other Docs

- `AGENTS.md`
  - defines how agents should use tasks
- `CONTEXT.md`
  - holds stable project facts
- `STATUS.md`
  - tells you which task is active now
- `DECISIONS.md`
  - records confirmed choices that outlive a single task
- `docs/`
  - holds long-form references that tasks can link to
