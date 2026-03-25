# Task: stage-d-02-public-demo-foundation-and-guardrails

## Goal

Establish the foundation and guardrails required for a real public internet demo.

## Project Stage

- Stage: Stage D
- Track: Delivery and Operations with required Platform Reliability support

## Why

The system is still primarily local or staging-oriented. Before deeper module productization continues, the repository
needs a public demo path that outside users can access without hidden setup and without unsafe operational assumptions.

## Context

Relevant documents:

- `docs/prd/STAGE_D_PLAN.md`
- `docs/prd/LONG_TERM_ROADMAP.md`
- `docs/development/DELIVERY_BASELINE.md`
- `docs/development/STAGING_RELEASE_PATH.md`
- `STATUS.md`

## Flow Alignment

- Flow A / B / C / D: delivery, auth, workspace access, and public-demo entry
- Related APIs: auth, workspaces, module discovery, health
- Related schema or storage changes: minimal only if required for bounded demo access and operator visibility

## Dependencies

- Prior task: `tasks/archive/stage-d/stage-d-01-task-stack-planning.md`
- Blockers: none

## Scope

Allowed files:

- `server/app/`
- `server/tests/`
- `web/app/`
- `web/components/`
- `web/lib/`
- `scripts/`
- `docs/development/`
- `README.md`
- `STATUS.md`
- `DECISIONS.md`

Disallowed files:

- enterprise auth or billing systems
- unrelated scenario-workflow deepening that belongs in later stages

## Deliverables

- Code or contract changes:
  - minimum public-demo auth and access guardrails
  - demo-safe failure handling and operator-visible limits where required
- Docs changes:
  - public-demo baseline and operator rules

## Acceptance Criteria

- the repository has a bounded public-demo access path
- public-demo limits are explicit instead of implied
- the operator has enough visibility and control to keep the demo usable

## Verification Commands

- Backend:
  - `cd server`
  - `..\\.venv\\Scripts\\python.exe -m pytest tests`
- Frontend:
  - `npm --prefix web run verify`

## Tests

- Normal case:
  - a new outside user can reach the public demo entry and sign in through the intended path
- Edge case:
  - the demo rejects or bounds unsupported access patterns clearly
- Error case:
  - failures do not silently look like successful public-demo onboarding

## Risks

- public access work can easily expand into full SaaS hardening if scope is not kept tight

## Rollback Plan

- revert the public-demo-specific access and guardrail additions while preserving the pre-existing local and staging flows
