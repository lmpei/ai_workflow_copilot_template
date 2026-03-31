# Multi-Subdomain Deployment

## Intent

This repository is no longer the long-term codebase for the root `lmpai.online` homepage. The intended commercial
shape is:

- `lmpai.online`
  - separate personal homepage deployment
- `weave.lmpai.online`
  - product frontend from this repository
- `api.lmpai.online`
  - backend API from this repository

The recommended edge is:

- Cloudflare -> shared host-level Caddy -> multiple services

## Why This Shape

- the root homepage and the product can deploy independently
- the product frontend and backend can roll forward or back independently of the homepage
- API routing is explicit instead of being hidden behind one mixed host
- only the shared edge exposes public `80/443`
- product services stay bound to loopback-only ports on the host

## This Repo's Deployment Path

For the product stack from this repo:

1. copy `.env.weave.example` outside git
2. start the stack with:
   - `docker compose -f docker-compose.weave-stack.yml --env-file <env-file> up -d --build`
3. place the shared Caddy config from `deploy/shared-caddy/Caddyfile.weave.example` into the host-level Caddy service
4. point Cloudflare DNS at the host

## Ports

The stack in this repo binds only loopback-facing ports by default:

- frontend: `127.0.0.1:3001 -> 3000`
- backend API: `127.0.0.1:8001 -> 8000`

That means:

- the product frontend is not directly public
- the backend API is not directly public
- Caddy is the only public ingress layer

## CORS

The backend should allow only the product frontend origin for browser traffic:

- `CORS_ORIGINS=https://weave.lmpai.online`

If more product hosts are added later, treat them as explicit additions instead of widening CORS by default.

## Reverse Proxy Headers

The backend deployment path now expects forwarded headers from the edge:

- `X-Forwarded-Proto`
- `X-Forwarded-Host`
- `X-Real-IP`

`server/Dockerfile.deploy` now starts Uvicorn with explicit proxy-header support so requests remain correct behind
Caddy.

## Compatibility Note

The older single-stack public-demo rollout path under `docker-compose.public-demo.yml` and the historical
`app.lmpai.online` rollout evidence remain in the repo as historical delivery records. They are no longer the preferred
commercial deployment boundary for this repository.
