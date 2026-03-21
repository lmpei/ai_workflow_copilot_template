# Stage B Staging Release Evidence Template

Copy this template outside git when you want a lightweight but durable record of what the Stage B rehearsal actually
verified.

If you use `scripts\staging-rehearse-windows.cmd`, it can generate a filled evidence record automatically. This
template exists so the expected evidence shape stays visible even when the helper is not used.

## Evidence Metadata

- Completed At:
- Release Owner:
- Env File:
- Service Mode:
- Change Ref:
- Rollback Target:
- Companion Handoff File:

## Automated Routine Captured

- `scripts\release-check-windows.cmd <env-file>`
- `docker compose --env-file <env-file> config`
- `docker compose --env-file <env-file> up -d --build ...`
- `scripts\migrate-windows.cmd <env-file>`
- `docker compose --env-file <env-file> up -d --build --force-recreate server worker web`
- `scripts\staging-smoke-windows.cmd <env-file>`

## Verified Targets

- API Health URL:
- Web Root URL:

## Manual Smoke Record

- [ ] login succeeds
- [ ] a workspace loads
- [ ] the documents view loads without server errors
- [ ] a Research task can run to completion
- [ ] the formal Research report path can complete
- [ ] traces and task history remain visible after the run

## Evidence Notes

- What changed:
- What was verified beyond the automated checks:
- Anything unusual observed:
- Follow-up needed before wider use: