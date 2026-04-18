# Task: AI Hot Tracker Report Scroll And Panel Polish

## Goal

Tighten the `AI 热点追踪` report page one more pass by making the report and follow-up surfaces truly split, internally scrollable, and visually cleaner at the bottom edge.

## Project Phase

- Phase: Post-Stage-K bounded follow-through
- Scenario module: `AI 热点追踪`

## Why

The first layout pass still left two problems visible in use:

- the right `追问` panel showed a clipped bottom edge
- mouse-wheel scrolling did not feel like each module owned its own scrollable area

This pass makes the split layout structurally correct instead of relying on surface-level spacing tweaks.

## Context

Relevant modules:

- `web/components/research/ai-hot-tracker-workspace.tsx`

## Scope

Allowed files:

- `web/components/research/`
- control-plane docs

Disallowed files:

- backend report generation
- deployment and environment files

## Deliverables

- Code changes:
  - split the report page into fixed shells with internal scroll bodies
  - keep the report footer fixed inside the left module
  - keep the follow-up composer fixed inside the right module
  - hide module scrollbars while preserving wheel scroll behavior
- Docs changes:
  - update `STATUS.md`

## Verification

- Frontend:
  - `npm --prefix web run verify`

## Outcome

- left report now scrolls inside its own body
- right follow-up panel now scrolls inside its own body
- the clipped right-panel bottom edge is reduced by moving the quick actions into the scroll body and keeping the composer as a separate bottom block
