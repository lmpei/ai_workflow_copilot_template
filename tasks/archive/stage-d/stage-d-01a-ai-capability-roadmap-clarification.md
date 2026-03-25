# Task: stage-d-01a-ai-capability-roadmap-clarification

## Goal

Clarify the AI capability portion of the long-term roadmap so it becomes a staged learning and adoption map instead of a
high-level concept list.

## Project Stage

- Stage: Stage D
- Track: cross-track planning refinement

## Why

The first version of the long-term roadmap captured the correct direction, but the AI capability section was still too
coarse. It needed a clearer structure showing capability families, likely sequencing, repository touchpoints, learning
questions, and exit signals.

## Context

Relevant documents:

- `docs/prd/LONG_TERM_ROADMAP.md`
- `docs/prd/STAGE_D_PLAN.md`
- `docs/prd/PLATFORM_PRD.md`
- `STATUS.md`
- `DECISIONS.md`

## Flow Alignment

- Flow A / B / C / D: planning support for all future capability waves
- Related APIs: none directly
- Related schema or storage changes: none

## Dependencies

- Prior task: `tasks/archive/stage-d/stage-d-01-task-stack-planning.md`
- Blockers: none

## Scope

Allowed files:

- `docs/prd/`
- `STATUS.md`
- `DECISIONS.md`
- `tasks/`

Disallowed files:

- runtime feature code
- unrelated deployment changes

## Deliverables

- Docs changes:
  - clarify the AI capability roadmap in `docs/prd/LONG_TERM_ROADMAP.md`
- Task changes:
  - archive this planning-refinement task after completion

## Acceptance Criteria

- the AI capability roadmap is organized into coherent waves instead of one broad theme
- each wave explains why it matters, where it touches the repository, and what would count as learning completion
- the clarified roadmap stays separate from the bounded Stage D execution plan

## Verification Commands

- Repository:
  - manual doc consistency review

## Tests

- Normal case:
  - a collaborator can understand the capability sequencing without inferring it from chat history
- Edge case:
  - the clarified roadmap does not overload Stage D with later AI-capability work
- Error case:
  - the roadmap does not imply that every trendy AI capability must be implemented immediately

## Risks

- making the roadmap too detailed could accidentally turn it into a pseudo-commitment rather than a learning guide

## Rollback Plan

- revert the roadmap clarification while preserving the broader long-term direction and bounded Stage D plan

## Results

- clarified the AI capability roadmap into explicit adoption waves
- added repository touchpoints, learning questions, and exit signals for each wave
- kept the capability roadmap separate from the bounded Stage D execution scope

## Execution Status

- Status: completed
- Completed At: 2026-03-26
- Notes: the long-term roadmap now gives a clearer AI capability learning path without changing the active Stage D implementation task

## Verification Result

- manual doc consistency review
