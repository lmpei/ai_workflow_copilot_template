# Stage H-05: Runtime Upload Storage Ignore Cleanup

## Why

The repository still tracked a few files under `server/storage/uploads/`, even though that directory is runtime upload
state and not durable source content. This made local runtime churn show up in normal feature work.

## Scope

- add one ignore rule for `server/storage/uploads/`
- remove already tracked upload files from the Git index without treating them as source deletions
- record the runtime-only boundary in the control-plane docs

## Non-Goals

- changing deployed volume behavior
- deleting server-side public data
- changing the active Stage H Research pilot scope

## Deliverables

- `server/storage/uploads/` ignored by Git going forward
- tracked upload files removed from the repository index
- control-plane docs updated to reflect the runtime-only boundary

## Verification

- `git diff --check`
- manual control-plane consistency review

## Completion Criteria

- local upload files no longer appear as repo changes during normal runtime use
- the repo documents `storage/uploads` as runtime state instead of source content
