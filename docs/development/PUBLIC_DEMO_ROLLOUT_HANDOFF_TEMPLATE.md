# Stage D Public Demo Rollout Handoff Template

Copy this template outside git when you want a short human-readable handoff note for the public-demo rollout rehearsal.

If you use `scripts\public-demo-rehearse-windows.cmd`, it can generate a filled handoff note automatically. This
template exists so the expected shape stays visible even when the helper is not used.

## Rehearsal Metadata

- Completed At:
- Operator:
- Env File:
- Service Mode:
- Change Ref:
- Rollback Target:
- Public Web URL:
- Public API Base URL:
- Evidence File:

## Automated Steps Completed

- `scripts\release-check-windows.cmd <env-file>`
- `scripts\public-demo-deploy-windows.cmd <env-file> <service-mode>`
- `scripts\public-demo-smoke-windows.cmd <env-file>`

## Manual Smoke Still Required

- login succeeds
- `Workspace Hub` loads
- guided demo workspace creation succeeds
- the seeded workspace overview shows the guided showcase panel
- one seeded path reaches `Documents -> Chat -> Tasks`

## Handoff Notes

- What was launched:
- What was verified beyond the automated checks:
- Anything unusual observed:
- Follow-up needed before wider sharing:
