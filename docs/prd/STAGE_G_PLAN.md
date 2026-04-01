# Stage G Plan

## Stage Name

`Stage G: Multi-Subdomain Product Split and Shared Edge Routing`

## Status

- Status: complete and closed
- Opened At: 2026-04-01
- First Task Wave: complete

## Position In The Project

Stage G begins after the Stage F experience reset. Stage F rebuilt the visible product surfaces, but the repository was
still carrying one temporary boundary that no longer matches the intended commercial deployment model: the same codebase
still behaved like it owned both the root homepage and the product entry route. Stage G corrects that deployment and
host-boundary problem.

## Stage Goal

Prepare this repository to run as the dedicated product stack behind:

- `weave.lmpai.online` for the product frontend
- `api.lmpai.online` for the backend API

while treating:

- `lmpai.online` as a separate root marketing site that is deployed outside this repository

## Primary Outcome

The repo should become product-only at the web tier and should ship one shared-edge deployment path that fits:

- Cloudflare -> Caddy -> multiple services
- host-based routing
- separate frontend and backend service deployment
- an independent API hostname
- no direct public exposure of app-service ports
- explicit reverse-proxy header handling
- explicit CORS handling for the product frontend host

## First Task Wave

1. `tasks/archive/stage-g/stage-g-02-weave-subdomain-product-split.md`

## Closeout

Stage G is complete after the repository boundary and live deployment boundary were aligned:

- `lmpai.online` is now treated as a separate homepage outside this repo
- this repo now serves the dedicated product host at `weave.lmpai.online`
- this repo now serves the dedicated API host at `api.lmpai.online`
- the shared Cloudflare -> Caddy -> multi-service edge is live

The next bounded planning unit is `docs/prd/STAGE_H_PLAN.md`.
