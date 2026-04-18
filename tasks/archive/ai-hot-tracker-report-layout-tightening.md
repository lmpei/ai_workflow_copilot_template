# Task: AI Hot Tracker Report Layout Tightening

## Goal

Rework the `AI 热点追踪` result page so the report and follow-up modules feel balanced, compact, and readable.

## Project Phase

- Phase: Post-Stage-K bounded follow-through
- Scenario module: `AI 热点追踪`

## Why

The current report page still carries uneven spacing, oversized type, and a visibly clipped right follow-up panel. It needs a tighter, product-grade split layout.

## Context

Relevant modules, dependencies, and related specs:

- `web/components/research/ai-hot-tracker-workspace.tsx`

## Flow Alignment

- Flow A:
  - user opens a generated `AI 热点追踪` report
- Flow B:
  - left report area scrolls internally with a hidden scrollbar
- Flow C:
  - right `追问` module stays visually clean and scrolls internally without a visible scrollbar

## Dependencies

- Prior task:
  - `tasks/archive/auth-overlay-overflow-fix.md`
- Blockers:
  - none inside the repo

## Scope

Allowed files:

- `web/components/research/`
- control-plane docs

Disallowed files:

- backend report-generation behavior
- deployment and environment files

## Deliverables

- Code changes:
  - rebalance report layout, spacing, and typography
  - fix follow-up panel clipping
  - ensure both report and follow-up surfaces have internal hidden scroll behavior
- Test changes:
  - frontend verify pass
- Docs changes:
  - update `STATUS.md` after completion

## Acceptance Criteria

- report page looks tighter and more deliberate
- right `追问` module no longer shows a clipped edge
- report and follow-up surfaces scroll internally without obvious scrollbars
- frontend verification passes

## Verification Commands

- Frontend:
  - `npm --prefix web run verify`

## Risks

- tightening the split layout can reveal spacing issues in long-content reports

## Rollback Plan

- restore the previous report and follow-up layout styles
