# Task

- ID: TEMP-2026-04-17-AI-HOT-TRACKER-HERO
- Title: tighten AI hot tracker empty-state hero hierarchy
- Status: completed

## Goal

Refine the empty-state first screen for `AI 热点追踪` so it feels more focused:

1. remove the top utility row from the empty-state view
2. promote `Ai热点` into the primary small hero label
3. reduce the visual dominance of `这一轮，有什么值得关注？`

## Scope

- change empty-state-only layout and typography in the dedicated hot-tracker surface
- keep the report state untouched

## Verification

- `npm --prefix web run verify`
- `git diff --check`
