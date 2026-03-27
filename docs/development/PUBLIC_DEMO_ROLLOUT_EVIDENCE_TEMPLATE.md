# Stage D Public Demo Rollout Evidence Template

Copy this template outside git when you want a durable record of what the first public-demo rollout rehearsal actually
checked.

If you use `scripts\public-demo-rehearse-windows.cmd`, it can generate a filled evidence record automatically. This
template exists so the expected evidence shape stays visible even when the helper is not used.

## Evidence Metadata

- Completed At:
- Operator:
- Env File:
- Service Mode:
- Change Ref:
- Rollback Target:
- Public Web URL:
- Public API Base URL:
- Companion Handoff File:

## Automated Routine Captured

- `scripts\release-check-windows.cmd <env-file>`
- `scripts\public-demo-deploy-windows.cmd <env-file> <service-mode>`
- `scripts\public-demo-smoke-windows.cmd <env-file>`

## Verified Targets

- API Health URL:
- Public Demo Settings URL:
- Public Demo Templates URL:
- Web Root URL:
- Login URL:
- Workspace URL:

## Manual Smoke Record

- [ ] login succeeds
- [ ] `Workspace Hub` loads
- [ ] guided demo workspace creation succeeds
- [ ] the seeded workspace overview shows the guided showcase panel
- [ ] one seeded path reaches `Documents -> Chat -> Tasks`

## External Prerequisites Used

- VM host:
- DNS / TLS status:
- Env file location:

## Evidence Notes

- What was launched:
- Which automated checks passed:
- Which manual checks passed:
- Anything unusual observed:
- Follow-up needed before wider sharing:
