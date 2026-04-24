# Task: AI Hot Tracker Judgment Quality And Internal Cleanup

## Goal

Strengthen `AI 热点追踪` as the primary strong-agent product loop by improving judgment inspectability,
cleaning internal hot-tracker-only contracts, tightening run-bound follow-up, and removing obvious legacy or duplicated
implementation paths.

## Scope

- Clean the hot-tracker schema layer so the current brief contract, tracking profile defaults, evaluation payloads, and
  degraded or failed copy all live in one canonical definition.
- Remove duplicated helper or fallback logic in hot-tracker services, especially around report generation and failed-run
  handling.
- Tighten the follow-up path so answers stay grounded to the current run, current event memory, and current blindspots.
- Simplify the hot-tracker report alias path so it resolves onto the canonical tracking-run flow instead of preserving
  a second response-shape branch.
- Clean the visible hot-tracker workspace copy for runtime state, evaluation, follow-up, history, and settings so the
  consumer path reads like one coherent product surface.
- Update backend tests that cover run creation, alias behavior, evaluation, and follow-up grounding.

## Out Of Scope

- No new module implementation for `Support Copilot` or `Job Assistant`
- No new source families beyond the current allowlist
- No user-defined source input
- No deployment or environment changes

## Verification

- Backend: `cd server` then `..\\.venv\\Scripts\\python.exe -m pytest tests`
- Frontend: `npm --prefix web run verify`
