# Stage I-13: MCP Trace and Review Visibility

## Why

If Stage I adds one real MCP-backed Research path, that path should end with the same level of trace and operator
review honesty already expected from the connector-backed baseline.

## Scope

- surface MCP use clearly in trace and review layers
- keep the checks bounded to the same Research-first pilot
- verify denied, degraded, and no-data MCP paths remain visible

## Non-Goals

- a generic cross-module audit redesign
- full optimization flywheel work
- broader Wave 3 orchestration review

## Deliverables

- one MCP-aware review baseline for the bounded Research path
- one operator-facing surface that exposes MCP use and degraded behavior
- docs and control-plane updates

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests`
- `npm --prefix web run verify`
- `git diff --check`

## Completion Criteria

- operators can tell when MCP-backed context was attempted and what happened
- denied or unavailable MCP behavior is visible instead of implicit
- Stage I can then be judged on a real MCP-backed baseline rather than on connector language alone
