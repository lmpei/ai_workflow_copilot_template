# Stage I-04: Connector Trace and Consent Visibility

## Why

The first connector pilot should not ship unless connector use, permission state, and degraded outcomes are visible in
trace and review surfaces.

## Scope

- surface connector usage and consent state in traces or review records
- expose honest degraded outcomes for denied, unavailable, or empty external context
- keep the operator-facing review path bounded to the pilot

## Non-Goals

- a full cross-module trust platform redesign
- automatic optimization loops
- broad audit platform work beyond the pilot

## Deliverables

- one connector-aware trace or review baseline
- one operator-visible surface for the pilot's connector behavior
- docs and control-plane updates

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests`
- `npm --prefix web run verify`
- `git diff --check`

## Completion Criteria

- connector usage and permission state are visible enough for honest operator review
- the pilot ends with explicit trace and degraded-path visibility instead of only a happy-path demo
