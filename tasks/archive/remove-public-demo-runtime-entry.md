# Task: remove-public-demo-runtime-entry

## Goal

Remove the legacy public-demo runtime entry path so homepage module entry always uses the real workspace creation flow in both local and deployed environments.

## Project Phase

- Phase: Phase 5 baseline refinement
- Scenario module: research / homepage module entry

## Why

The current homepage `AI 热点追踪` entry still bootstraps a seeded public-demo workspace before navigation. That creates environment-specific behavior, misleading errors, and drift between local and production entry paths.

## Context

Relevant surfaces:

- `web/components/workspace/workspace-center-panel.tsx`
- `web/lib/api.ts`
- `server/app/services/workspace_service.py`
- `server/app/services/public_demo_service.py`
- `server/app/api/routes/public_demo.py`
- control-plane docs in `STATUS.md`, `DECISIONS.md`, `ARCHITECTURE.md`

## Flow Alignment

- Flow A / Homepage module entry: use canonical workspace creation only
- Flow B / Workspace limits: remove public-demo runtime gating from normal workspace creation
- Related APIs: `POST /api/v1/workspaces`
- Related schema or storage changes: none

## Dependencies

- Prior task: deploy automation and rollback baseline
- Blockers: none

## Scope

Allowed files:

- `web/components/workspace/workspace-center-panel.tsx`
- `web/lib/api.ts`
- `server/app/services/workspace_service.py`
- `server/app/services/public_demo_service.py`
- `server/app/api/routes/public_demo.py`
- `server/tests/`
- `STATUS.md`
- `DECISIONS.md`
- `ARCHITECTURE.md`

Disallowed files:

- deployment and environment files
- module product names

## Deliverables

- Code changes: remove homepage runtime dependence on public demo bootstrap and align canonical workspace entry flow
- Test changes: cover normal workspace creation path without public-demo runtime coupling
- Docs changes: record the removal in control-plane docs

## Acceptance Criteria

- Homepage module entry no longer calls public-demo template workspace creation
- Local and production both enter modules through the same real workspace creation path
- Public-demo runtime limits no longer block normal workspace creation
- Tests pass
- Frontend verify passes

## Verification Commands

- Backend:
  - `cd server`
  - `..\\.venv\\Scripts\\python.exe -m pytest tests`
- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case: homepage creates and opens a regular research workspace
- Edge case: authenticated user with existing workspaces can still create a new workspace through the canonical path
- Error case: workspace creation failure surfaces as a workspace creation error, not a demo bootstrap error

## Risks

- Legacy public-demo routes may still exist for unused surfaces and become dead code if not cleaned carefully

## Rollback Plan

- Revert the task commit and redeploy the previous known-good release
