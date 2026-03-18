# Stage B Staging Handoff Template

Copy this template outside git when you want a human-readable staging rehearsal record.

If you use `scripts\staging-rehearse-windows.cmd`, it will generate a filled handoff note automatically. This template
exists so the expected shape stays visible even when the helper is not used.

## Rehearsal Metadata

- Completed At:
- Release Owner:
- Env File:
- Service Mode:
- Change Ref:
- Rollback Target:

## Automated Steps Completed

- `scripts\release-check-windows.cmd <env-file>`
- `docker compose --env-file <env-file> up -d --build ...`
- `scripts\migrate-windows.cmd <env-file>`
- `docker compose --env-file <env-file> up -d --build --force-recreate server worker web`
- `scripts\staging-smoke-windows.cmd <env-file>`

## Manual Smoke Still Required

- login succeeds
- a workspace loads
- the documents view loads without server errors
- a Research task can run to completion
- the formal Research report path can complete
- traces and task history remain visible after the run

## Handoff Notes

- What changed:
- What was verified beyond the automated checks:
- Anything unusual observed:
- Follow-up needed before wider use:
