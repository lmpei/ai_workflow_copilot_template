# Stage I-21: Remote MCP Auth and Review Closeout

## Why

The repo should not claim a true external MCP baseline unless credential or auth boundaries, endpoint identity, and
remote failure shapes remain explicit in operator-facing review.

## Scope

- make endpoint identity, auth state, and remote failure detail visible in traces and review
- keep the checks bounded to the same Research-first pilot
- verify the product degrades honestly when the true external MCP endpoint is denied, misconfigured, or unavailable

## Non-Goals

- generic cross-module audit redesign
- broad connector admin UI
- Wave 3 orchestration review

## Deliverables

- one true-external-MCP-aware review baseline for the bounded Research path
- one operator-facing surface that exposes endpoint identity, auth state, and remote degraded behavior
- docs and control-plane updates for Stage I closeout readiness

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests`
- `npm --prefix web run verify`
- `git diff --check`

## Completion Criteria

- operators can tell which external MCP endpoint was used and what happened
- auth-required, auth-denied, misconfigured, unavailable, and no-data behavior are visible instead of implicit
- Stage I can then be judged on one true external MCP baseline instead of only on the current repo-local subprocess
  baseline
