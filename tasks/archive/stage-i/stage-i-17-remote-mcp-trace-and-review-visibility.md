# Stage I-17: Remote MCP Trace and Review Visibility

## Why

If the repo adds one true out-of-process MCP path, that path should end with the same level of operator visibility now
expected from the bounded local MCP baseline.

## Scope

- surface transport-aware MCP behavior clearly in traces and review layers
- keep the checks bounded to the same Research-first pilot
- verify denied, degraded, unavailable, and no-data remote MCP paths remain visible

## Non-Goals

- generic cross-module audit redesign
- full optimization flywheel work
- broader Wave 3 orchestration review

## Deliverables

- one remote-MCP-aware review baseline for the bounded Research path
- one operator-facing surface that exposes remote MCP use and degraded behavior
- docs and control-plane updates

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests`
- `npm --prefix web run verify`
- `git diff --check`

## Completion Criteria

- operators can tell when remote MCP-backed context was attempted and what happened
- transport failure, denial, and no-data behavior are visible instead of implicit
- Stage I can then be judged on a true out-of-process MCP baseline instead of only on the current local-MCP baseline
