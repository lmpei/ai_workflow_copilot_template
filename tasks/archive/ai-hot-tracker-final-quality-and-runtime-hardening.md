# Task: AI Hot Tracker Final Quality and Runtime Hardening

## Goal

Push `AI 热点追踪` closer to its strong-agent end state by hardening judgment quality, runtime state visibility,
follow-up grounding evidence, and the remaining canonical-path cleanup.

## Why

The current hot-tracker loop already has trusted intake, ranking, clustering, delta, event memory, saved runs,
grounded follow-up, and an internal evaluation view. What it still lacks is stronger inspectability and runtime truth:
judgment checks are not yet machine-readable, follow-up answers do not persist their grounding metadata, signal memory
cannot yet express streak or cooling windows cleanly, and the workspace state does not expose the last saved brief time
or the last meaningful update time.

## Scope

- Extend hot-tracker tracking state and signal memory with the extra runtime and continuity fields required by the end-state spec.
- Extend evaluation output with machine-readable quality or judgment findings.
- Extend hot-tracker follow-up persistence with bounded grounding metadata so evaluation can inspect what answers relied on.
- Surface the richer runtime state and evaluation checks on the dedicated hot-tracker frontend.
- Keep the hot-tracker path canonical; do not reopen generic Research-era response branches.

## Out Of Scope

- No new module work outside `AI 热点追踪`.
- No user-defined sources.
- No generic public crawling.
- No full-article media crawling.
- No external notification center or stand-alone alert inbox.
- No separate debug console outside the existing `?view=evaluation` path.

## Verification

- Backend: `cd server` then `..\\.venv\\Scripts\\python.exe -m pytest tests`
- Frontend: `npm --prefix web run verify`
