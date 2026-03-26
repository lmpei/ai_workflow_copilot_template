# Task: stage-d-03-demo-content-seeding-and-showcase-path

## Goal

Create the sample content, workspace path, and public showcase flow that make the internet demo understandable to a
first-time user.

## Project Stage

- Stage: Stage D
- Track: Research as reference workflow with Delivery and Operations support

## Why

A public URL is not enough. The demo needs seeded content or clearly documented sample paths so a first-time user can
reach meaningful workflow value quickly instead of landing in an empty shell.

## Context

Relevant documents:

- `docs/prd/STAGE_D_PLAN.md`
- `docs/prd/LONG_TERM_ROADMAP.md`
- `docs/development/STAGE_C_CROSS_MODULE_READINESS.md`
- `README.md`

## Flow Alignment

- Flow A / B / C / D: workspace entry, documents, modules, tasks, evals, traces
- Related APIs: workspaces, documents, tasks, evals
- Related schema or storage changes: only what is required for seeded demo-safe content

## Dependencies

- Prior task: `tasks/stage-d-02-public-demo-foundation-and-guardrails.md`
- Blockers: `stage-d-02` public-demo baseline

## Scope

Allowed files:

- `server/app/`
- `server/tests/`
- `web/app/`
- `web/components/`
- `web/lib/`
- `scripts/`
- `docs/`
- `README.md`
- `STATUS.md`
- `DECISIONS.md`

Disallowed files:

- deep new module productization beyond the existing Stage C workflow depth
- unrelated infrastructure expansion

## Deliverables

- Code or contract changes:
  - sample content or seeding support required for a repeatable demo path
  - clear public-facing entry and showcase flow
- Docs changes:
  - explain how the demo should be exercised by a first-time collaborator

## Acceptance Criteria

- a first-time user can reach meaningful module value quickly after login
- the demo path highlights real workflow depth rather than empty surfaces
- the repository has one repeatable showcase flow for public use

## Verification Commands

- Backend:
  - `cd server`
  - `..\\.venv\\Scripts\\python.exe -m pytest tests`
- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - a new user can follow the intended showcase path without hidden knowledge
- Edge case:
  - missing demo content is surfaced clearly rather than silently producing a hollow experience
- Error case:
  - seeded demo flows do not pretend to be user-generated or production-scale data

## Risks

- showcase content can drift into fake product polish if it stops reflecting the system's real capabilities

## Rollback Plan

- revert the seeded-content and showcase-flow additions while preserving the public-demo foundation
