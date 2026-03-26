# Task: stage-d-06-public-hosting-target-and-deployment-contract

## Goal

Choose and fix in text the bounded public hosting target, deployment shape, environment contract, and rollout assumptions
for the first real internet-accessible demo.

## Project Stage

- Stage: Stage D
- Track: Delivery and Operations with required Platform Reliability support

## Why

The repository now has a real public-demo baseline, but it still lacks one explicit answer to the next practical
question: where and how will the first internet-accessible environment actually run.

## Context

Relevant documents:

- `docs/prd/STAGE_D_PLAN.md`
- `docs/prd/LONG_TERM_ROADMAP.md`
- `docs/development/PUBLIC_DEMO_BASELINE.md`
- `docs/development/PUBLIC_DEMO_SHOWCASE_PATH.md`
- `docs/development/PUBLIC_DEMO_OPERATOR_RUNBOOK.md`
- `docs/development/DELIVERY_BASELINE.md`
- `docs/development/STAGING_RELEASE_PATH.md`
- `README.md`
- `STATUS.md`

## Flow Alignment

- Flow D: public-demo deployment target selection and deployment contract
- Related APIs: health, auth, public-demo, workspace access
- Related schema or storage changes: none unless minimally required to clarify the deployment contract

## Dependencies

- Prior task: `tasks/archive/stage-d/stage-d-05-wave-two-planning.md`
- Blockers: completed Stage D wave one baseline

## Scope

Allowed files:

- `README.md`
- `CONTEXT.md`
- `STATUS.md`
- `DECISIONS.md`
- `docs/prd/`
- `docs/development/`
- `tasks/`
- `scripts/`

Disallowed files:

- unrelated module workflow expansion
- unbounded production-ops automation
- live secret or provider rotation

## Deliverables

- Docs changes:
  - one explicit hosting target recommendation or selection
  - one bounded deployment shape for web, API, worker, database, Redis, and vector store
  - explicit env-file and secret expectations for the first real internet rollout
  - smoke and rollback assumptions for that target
- Code or script changes:
  - only the minimum script or doc support needed to reflect the chosen deployment contract

## Acceptance Criteria

- the repo states one bounded first public hosting target instead of leaving deployment abstract
- the environment contract for the first rollout is explicit enough that the next task can wire it without guessing
- rollout and rollback expectations are stated honestly for the chosen target

## Verification Commands

- Repository:
  - manual doc consistency review
- Optional script help verification if scripts change

## Tests

- Normal case:
  - a collaborator can identify the intended first public hosting shape without consulting chat history
- Edge case:
  - the contract stays bounded and does not expand into a full production platform design
- Error case:
  - no doc should imply that the first public rollout target is already deployed if it is only selected and documented

## Risks

- selecting a target that is too ambitious could delay the actual internet rollout instead of clarifying it

## Rollback Plan

- revert the hosting-target and deployment-contract docs while preserving the earlier public-demo baseline