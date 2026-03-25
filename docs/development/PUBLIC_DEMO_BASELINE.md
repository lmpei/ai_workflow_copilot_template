# Public Demo Baseline

## Purpose

This document defines the bounded public-demo rules introduced in `stage-d-02`.

The goal is to make the repository usable through a real internet-facing demo path without pretending the system is
already a production SaaS platform.

## What Stage D-02 Adds

The public-demo foundation now includes:

- a backend-owned `/api/v1/public-demo` settings endpoint
- demo-mode registration control
- bounded workspace creation per account
- bounded document uploads per workspace
- bounded task creation per workspace
- bounded upload size checks
- matching public-demo notices in the home, auth, and workspace entry surfaces

## Current Guardrails

These settings are controlled in `server/app/core/config.py`.

- `PUBLIC_DEMO_MODE`
  - enables public-demo guardrails when set to `true`
- `PUBLIC_DEMO_REGISTRATION_ENABLED`
  - allows or blocks self-serve registration during a demo window
- `PUBLIC_DEMO_MAX_WORKSPACES_PER_USER`
  - current default: `3`
- `PUBLIC_DEMO_MAX_DOCUMENTS_PER_WORKSPACE`
  - current default: `12`
- `PUBLIC_DEMO_MAX_TASKS_PER_WORKSPACE`
  - current default: `30`
- `PUBLIC_DEMO_MAX_UPLOAD_BYTES`
  - current default: `5242880` (`5 MB`)

## Operator Rules

Use this baseline for public-demo operation:

1. keep public-demo limits explicit and user-visible
2. disable self-serve registration if the demo environment becomes unstable or overloaded
3. treat demo accounts and demo data as bounded disposable surfaces, not as durable production commitments
4. prefer clear failure messages over silent degradation when limits are hit
5. keep later Stage D work responsible for content seeding, showcase paths, and operator runbooks rather than overloading this baseline

## Public API Surface

The operator-visible public-demo contract is:

- `GET /api/v1/public-demo`

It returns:

- `public_demo_mode`
- `registration_enabled`
- `max_workspaces_per_user`
- `max_documents_per_workspace`
- `max_tasks_per_workspace`
- `max_upload_bytes`

## What This Baseline Does Not Promise

This baseline does not yet mean:

- production-grade abuse prevention
- billing, organizations, or enterprise auth
- multi-region or high-availability deployment
- permanent user data retention guarantees
- a fully polished public showcase path

Those concerns belong in later Stage D tasks and later stages.
