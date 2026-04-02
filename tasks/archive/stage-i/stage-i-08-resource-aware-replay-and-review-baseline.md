# Stage I-08: Resource-Aware Replay and Review Baseline

## Why

If the connector wave now includes explicit external resource snapshots and explicit consent lifecycle, the replay or
review layer should verify those new boundaries instead of only checking answer-time connector visibility.

## Scope

- extend replay or review rules to resource snapshots, selection visibility, and consent lifecycle outcomes
- keep the baseline bounded to the Research-first connector pilot
- preserve honest degraded and no-selection behavior

## Non-Goals

- full optimization flywheel work
- generic cross-module audit platform redesign
- broader MCP orchestration coverage

## Deliverables

- one resource-aware review or replay baseline for the bounded Research connector path
- one operator-facing surface for recent resource-backed runs
- docs and control-plane updates

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests`
- `npm --prefix web run verify`
- `git diff --check`

## Completion Criteria

- recent Research connector runs can be reviewed with explicit awareness of resource snapshots and consent lifecycle
- missing or inconsistent resource selection is visible to operators
- the second bounded Stage I wave ends with one clear replay or review contract
