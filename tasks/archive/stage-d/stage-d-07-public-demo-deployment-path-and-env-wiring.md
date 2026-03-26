# Task: stage-d-07-public-demo-deployment-path-and-env-wiring

## Goal

Implement the repository-side deployment path and environment wiring required by the chosen public hosting target.

## Project Stage

- Stage: Stage D
- Track: Delivery and Operations with required Platform Reliability support

## Why

A chosen hosting target still is not a real rollout path. The repository must expose the actual deployment steps,
environment expectations, and bounded scripts or config needed to bring the public demo online.

## Context

Relevant documents:

- `docs/prd/STAGE_D_PLAN.md`
- `docs/development/PUBLIC_DEMO_OPERATOR_RUNBOOK.md`
- `docs/development/DELIVERY_BASELINE.md`
- `docs/development/STAGING_RELEASE_PATH.md`
- the result of `tasks/stage-d-06-public-hosting-target-and-deployment-contract.md`

## Flow Alignment

- Flow D: deployment path, runtime wiring, smoke, restart, and bounded operator visibility
- Related APIs: health, auth, public-demo, guided-template catalog, workspace path
- Related schema or storage changes: only what is minimally required for the public rollout path

## Dependencies

- Prior task: `tasks/stage-d-06-public-hosting-target-and-deployment-contract.md`
- Blockers: explicit hosting target and deployment contract from `stage-d-06`

## Scope

Allowed files:

- `server/app/`
- `server/tests/`
- `web/`
- `scripts/`
- `docs/development/`
- `README.md`
- `STATUS.md`
- `DECISIONS.md`
- deployment-related repo files only if the chosen target requires them

Disallowed files:

- unrelated scenario-module expansion
- large-scale production automation beyond the bounded first public rollout

## Deliverables

- Code or contract changes:
  - only the minimum repository changes required to support the chosen public rollout path
- Docs changes:
  - deployment steps, env wiring expectations, and smoke checks for the chosen target

## Acceptance Criteria

- the repository contains one bounded deployment path for the chosen public hosting target
- the public-demo env and smoke expectations are explicit enough for a real rollout rehearsal
- the repo still stays honest about limited operational maturity

## Verification Commands

- Backend:
  - `cd server`
  - `..\.venv\Scripts\python.exe -m pytest tests`
- Frontend:
  - `npm --prefix web run verify`
- Scripts:
  - relevant `--help` or dry-run checks for any new deployment helpers

## Tests

- Normal case:
  - a collaborator can follow the documented deployment path without hidden tribal knowledge
- Edge case:
  - missing or misaligned env configuration fails clearly
- Error case:
  - the deployment docs do not imply that rollout is complete before the next rehearsal task executes it

## Risks

- deployment wiring can easily drift into provider-specific complexity if the target remains too broad

## Rollback Plan

- revert the deployment-path additions while preserving the earlier public-demo baseline and hosting contract docs