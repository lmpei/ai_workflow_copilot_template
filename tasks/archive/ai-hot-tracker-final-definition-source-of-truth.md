# Task: AI Hot Tracker Final Definition Source of Truth

## Goal

Create one durable long-form source of truth for the `AI 热点追踪` end-state definition and align the control-plane docs to reference it.

## Project Phase

- Phase: Phase 5 baseline complete
- Scenario module: AI hot tracker

## Why

The module's final definition has been agreed in conversation, but the repository still lacks one clean, readable, canonical document that future implementation and review can rely on.

## Context

The current repo state already treats `AI 热点追踪` as the first real single-agent product loop, but its final product and system definition is still scattered across control-plane summaries, archived tasks, and chat history.

## Flow Alignment

- AI hot tracker:
  - trusted source intake -> ranked and clustered signal judgment -> brief synthesis -> grounded follow-up -> internal evaluation
- Related docs:
  - `STATUS.md`
  - `CONTEXT.md`
  - `DECISIONS.md`
  - `ARCHITECTURE.md`
  - `docs/PROJECT_GUIDE.md`
  - `docs/prd/AI_FRONTIER_RESEARCH_CONTRACT.md`

## Dependencies

- Prior task: `tasks/archive/ai-hot-tracker-final-completion-line.md`
- Blockers: none inside the repo

## Scope

Allowed files:

- `docs/prd/AI_HOT_TRACKER_FINAL_DEFINITION.md`
- `docs/prd/AI_FRONTIER_RESEARCH_CONTRACT.md`
- `STATUS.md`
- `CONTEXT.md`
- `DECISIONS.md`
- `ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`
- task docs for this slice

Disallowed files:

- product runtime code
- deployment or environment files
- second-module implementation paths

## Deliverables

- Docs changes:
  - add one canonical long-form final-definition doc for `AI 热点追踪`
  - downgrade the old frontier-research contract into a historical pointer
  - align control-plane docs and doc navigation to reference the new source of truth

## Acceptance Criteria

- `docs/prd/AI_HOT_TRACKER_FINAL_DEFINITION.md` can stand alone as the final definition
- `docs/prd/AI_FRONTIER_RESEARCH_CONTRACT.md` no longer acts as a second main definition
- control-plane docs point to one shared definition source
- the new long-form doc and pointer doc are readable UTF-8 text without damaged strings

## Verification Commands

- Docs consistency review only:
  - inspect the new final-definition doc
  - inspect the downgraded pointer doc
  - search the repo for main-definition references to confirm one source of truth

## Tests

- Normal case
  - a contributor can find the final AI hot tracker definition from `docs/PROJECT_GUIDE.md` or control-plane docs
- Edge case
  - older references that still mention `AI_FRONTIER_RESEARCH_CONTRACT.md` now land on a historical pointer instead of a conflicting definition
- Error case
  - the repo no longer requires chat history to resolve what the end-state definition actually is

## Risks

- keeping too much content in the old contract file would recreate dual truth

## Rollback Plan

- revert the new final-definition doc and related control-plane doc edits together
