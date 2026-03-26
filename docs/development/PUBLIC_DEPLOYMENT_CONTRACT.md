# Public Deployment Contract

## Purpose

This document fixes the bounded hosting target chosen in `stage-d-06` for the first real internet-accessible demo.

It is not a production architecture. It is the simplest honest deployment shape that matches the current repository and
can be executed soon.

## Chosen First Hosting Target

The first public rollout target is:

- one small public Linux VM
- Docker Engine + Docker Compose on that VM
- one reverse-proxy layer with TLS termination
- the existing multi-container stack kept mostly intact

This means the first rollout does **not** assume:

- Kubernetes
- multi-region hosting
- managed platform-native rewrites of the stack
- autoscaling services
- zero-downtime deployment guarantees

## Why This Target

This target is chosen because it best matches the current repository shape:

- the repo already runs end to end with Docker Compose
- the backend, worker, Redis, Postgres, and Chroma already expect one shared networked stack
- the shortest path to a public URL is to preserve that shape rather than redesign for a more abstract hosting platform
- the project priority is to get to a real public demo soon, not to maximize infrastructure sophistication

## Service Shape

The target public environment keeps these services:

- `web`
  - public Next.js app
- `server`
  - public FastAPI API
- `worker`
  - private background worker
- `db`
  - private Postgres
- `redis`
  - private Redis
- `chroma`
  - private vector store
- `reverse-proxy`
  - public TLS terminator and host router

Only the reverse-proxy should expose internet-facing ports directly.

## Public URL Model

The bounded first URL model is:

- `https://app.<domain>`
  - public web UI
- `https://api.<domain>`
  - public API base

This shape is preferred over path-based multiplexing because it keeps the first rollout simpler:

- the web app can keep a clean root domain
- the API can keep an explicit base URL
- the existing `NEXT_PUBLIC_API_BASE_URL` contract already fits this model

## Internal Network Model

Inside the VM and Compose network:

- `web` talks to `server` through `INTERNAL_API_BASE_URL=http://server:8000/api/v1`
- `worker` talks to `server`, `db`, `redis`, and `chroma` through the internal Docker network
- `db`, `redis`, and `chroma` stay private to the VM or internal Docker network only

## Environment Contract

The first public rollout must use one environment-specific env file outside git.

Minimum required values:

- `APP_ENV_FILE`
- `APP_ENV=staging` or another explicit non-local environment label
- `AUTH_SECRET_KEY`
- live provider keys and model settings
- `NEXT_PUBLIC_API_BASE_URL=https://api.<domain>/api/v1`
- `INTERNAL_API_BASE_URL=http://server:8000/api/v1`
- `DATABASE_URL`
- `REDIS_URL`
- `CHROMA_URL`
- `CORS_ORIGINS` including `https://app.<domain>`
- `PUBLIC_DEMO_MODE=true`
- `PUBLIC_DEMO_REGISTRATION_ENABLED` set intentionally, not left implicit

## Persistence Contract

For the first public rollout:

- Postgres data must persist beyond container recreation
- Chroma data must persist beyond container recreation
- Redis may remain disposable if the operator accepts that queued in-flight work can be lost during refresh
- uploaded document storage must persist beyond container recreation

This implies the VM deployment needs explicit host-backed or named-volume persistence for:

- Postgres
- Chroma
- uploaded files under `storage/uploads`

## Reverse Proxy Contract

The first rollout should use one reverse proxy with automatic TLS where possible.

Required behavior:

- route `app.<domain>` to `web`
- route `api.<domain>` to `server`
- keep direct container ports off the public internet except the proxy entrypoint

The repo does not need to standardize the proxy implementation yet beyond that contract.
The next task may choose the lightest implementation that satisfies it.

## Smoke Contract

The first public rollout is not considered healthy unless these URLs behave correctly:

- `https://api.<domain>/api/v1/health`
- `https://api.<domain>/api/v1/public-demo`
- `https://api.<domain>/api/v1/public-demo/templates`
- `https://app.<domain>/`
- `https://app.<domain>/login`
- `https://app.<domain>/workspaces`

Manual smoke must also confirm:

- login works
- guided demo workspace creation works
- one seeded demo path can reach `Documents -> Chat -> Tasks`

## Rollback Contract

The first rollout rollback remains manual and bounded.

Minimum rollback expectation:

1. keep the previous known-good code or image reference
2. keep the current env file and previous env file revisions recoverable outside git
3. if rollout fails after app update, restore the prior app state and rerun smoke
4. if schema or storage state is incompatible, reconcile that state before retrying

This contract does not promise zero-downtime rollback.

## Explicit Non-Goals

This deployment contract does not yet cover:

- managed-database migration away from Compose
- horizontal scaling
- multi-VM networking
- platform-native secret management automation
- production-grade observability or incident automation

Those can come later if the public demo proves worth hardening further.