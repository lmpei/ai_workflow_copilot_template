# Stage D Public Demo Rollout Handoff Record

## Rehearsal Metadata

- Completed At: 2026-03-27
- Operator: human operator with coding-agent guidance
- Env File: `.env.public-demo` kept outside git on the target VM
- Service Mode: `full-stack`
- Change Ref: `9c68935`
- Rollback Target: redeploy `9c68935` with the preserved `.env.public-demo` file and current public-demo persistent volumes
- Public Web URL: `https://app.lmpai.online`
- Public API Base URL: `https://api.lmpai.online/api/v1`
- Evidence File: `docs/development/PUBLIC_DEMO_ROLLOUT_EVIDENCE_2026-03-27.md`

## Automated Steps Completed

- rendered `docker-compose.public-demo.yml` successfully with the live `.env.public-demo`
- built and started the bounded public-demo stack on the target VM
- ran `alembic upgrade head` through the live `server` container
- checked:
  - `https://api.lmpai.online/api/v1/health`
  - `https://api.lmpai.online/api/v1/public-demo`
  - `https://api.lmpai.online/api/v1/public-demo/templates`

## Manual Smoke Completed

- login succeeded
- `Workspace Hub` loaded
- guided demo workspace creation succeeded
- the seeded workspace overview showed the guided showcase panel
- one seeded path reached `Documents -> Chat -> Tasks`

## Handoff Notes

- What was launched:
  - the first real public-demo rehearsal for Stage D using the single-VM Docker Compose target
- What was verified beyond the automated checks:
  - public browser access to the web root, login page, and workspace page
  - first-time-user guided demo flow is usable through the live public URL
- Anything unusual observed:
  - the first live domain is `lmpai.online`, not the earlier placeholder domain used in planning discussion
  - Linux-host manual execution was used for the live rehearsal because the helper wrappers are Windows-oriented
- Follow-up needed before wider sharing:
  - preserve the current env file and deployed revision as the baseline rollback pair
  - use the existing refresh and smoke routine before future demos or interviews
  - keep the public demo described as bounded and demo-grade
