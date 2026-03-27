# Stage D Public Demo Rollout Evidence Record

## Evidence Metadata

- Completed At: 2026-03-27
- Operator: human operator with coding-agent guidance
- Env File: `.env.public-demo` kept outside git on the target VM
- Service Mode: `full-stack`
- Change Ref: `9c68935`
- Rollback Target: redeploy `9c68935` with the preserved `.env.public-demo` file and current public-demo persistent volumes
- Public Web URL: `https://app.lmpai.online`
- Public API Base URL: `https://api.lmpai.online/api/v1`
- Companion Handoff File: `docs/development/PUBLIC_DEMO_ROLLOUT_HANDOFF_2026-03-27.md`

## Execution Path Captured

The first bounded public-demo rehearsal used the Linux VM deployment path directly instead of the Windows helper
scripts.

Captured steps:

- `docker compose -f docker-compose.public-demo.yml --env-file .env.public-demo config`
- `docker compose -f docker-compose.public-demo.yml --env-file .env.public-demo up -d --build`
- `docker compose -f docker-compose.public-demo.yml --env-file .env.public-demo exec server python -m alembic upgrade head`
- `curl https://api.lmpai.online/api/v1/health`
- `curl https://api.lmpai.online/api/v1/public-demo`
- `curl https://api.lmpai.online/api/v1/public-demo/templates`

## Verified Targets

- API Health URL: `https://api.lmpai.online/api/v1/health`
- Public Demo Settings URL: `https://api.lmpai.online/api/v1/public-demo`
- Public Demo Templates URL: `https://api.lmpai.online/api/v1/public-demo/templates`
- Web Root URL: `https://app.lmpai.online/`
- Login URL: `https://app.lmpai.online/login`
- Workspace URL: `https://app.lmpai.online/workspaces`

## Manual Smoke Record

- [x] login succeeds
- [x] `Workspace Hub` loads
- [x] guided demo workspace creation succeeds
- [x] the seeded workspace overview shows the guided showcase panel
- [x] one seeded path reaches `Documents -> Chat -> Tasks`

## External Prerequisites Used

- VM host: Tencent Cloud Lighthouse Hong Kong VM `101.32.216.83`
- DNS / TLS status: Cloudflare active, `app` and `api` records routed to the VM, DNS-only proxy mode during rollout, SSL mode set to `Full (strict)`
- Env file location: git-external `.env.public-demo` on the target VM

## Evidence Notes

- What was launched:
  - the first bounded public-demo stack using `docker-compose.public-demo.yml` on the chosen single-VM target
- Which automated checks passed:
  - Compose config rendered successfully
  - public containers built and started successfully
  - Alembic upgrade completed successfully
  - public API health, settings, and template endpoints returned successfully
- Which manual checks passed:
  - the public web root loaded
  - login worked
  - `Workspace Hub` loaded
  - guided demo workspace creation worked
  - one seeded demo path reached `Documents -> Chat -> Tasks`
- Anything unusual observed:
  - the live public domain used for the first rehearsal is `lmpai.online`, replacing the earlier planning placeholder `impai.online`
  - the real rollout was executed directly on Linux rather than through the Windows-only helper wrappers
- Follow-up needed before wider sharing:
  - preserve the current `.env.public-demo` file and deployed revision as the first rollback baseline
  - decide whether to keep self-serve registration enabled as public traffic increases
  - keep the current demo honestly labeled as demo-grade, not production-grade
