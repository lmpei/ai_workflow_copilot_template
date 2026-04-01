# Stage G-02: Weave Subdomain Product Split

## Why

The current repository still carries temporary assumptions from the Stage F redesign period:

- the root `/` route still acts like a mixed personal-homepage and product boundary artifact
- deployment defaults still assume the older `app.<domain>` public-demo shape
- the repo does not yet expose one cleaner deployment path for a shared Cloudflare -> Caddy -> multi-service stack

The product now needs a clearer commercial boundary:

- `lmpai.online` should be the separate personal homepage outside this repo
- this repo should own the dedicated product frontend and backend deployment only

## Scope

- make the frontend root route behave as the dedicated product home for the product host
- keep `/app` only as a compatibility redirect instead of the canonical product entry
- update auth and workspace-center links so they no longer assume `/app` is the long-term product home
- add a dedicated deployment path for shared-edge subdomain routing with:
  - `weave.lmpai.online`
  - `api.lmpai.online`
- add product-facing env and Caddy examples for the shared-edge model
- make reverse-proxy header handling explicit on the backend deployment path
- make CORS expectations explicit for the split frontend and API hosts

## Non-Goals

- deploy the separate `lmpai.online` homepage from this repository
- remove or rewrite dated rollout evidence that truthfully records the older `app.lmpai.online` public-demo rollout
- redesign the module names
- change the backend business contracts

## Deliverables

- updated frontend entry routing and auth continuation behavior
- a new shared-edge deployment compose path for this repo
- a new env template and Caddy example for the subdomain split
- control-plane docs updated to reflect Stage G and the repo's new product-only host boundary

## Verification

- `npm --prefix web run verify`
- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests`
- `git diff --check`

## Completion Criteria

- the repo can be deployed as the dedicated `weave` product stack without owning the root homepage
- the deployment docs and templates consistently reflect `weave.lmpai.online` plus `api.lmpai.online`
- the repo's root web route now reads as the product home on the product host
