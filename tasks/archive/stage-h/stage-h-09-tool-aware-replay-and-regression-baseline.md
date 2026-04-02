# Stage H-09: Tool-Aware Replay and Regression Baseline

## Why

Background-capable Research analysis and bounded run memory should not ship without stronger replay and regression
discipline. The next bounded reliability step is to make the deeper Research path reviewable without pretending to have
already built a full optimization flywheel.

## Scope

- extend the current pilot review baseline into replayable or regression-friendly checks for the deeper Research run
  path
- keep tool-aware degraded-path honesty visible in those checks
- add only the minimum operator-facing surfacing needed for reliable review

## Non-Goals

- a full cross-module eval platform redesign
- broad benchmark unification across every workflow
- automatic prompt optimization loops

## Deliverables

- one stronger replay or regression baseline for the deeper Research run path
- one operator-visible review path for tool-aware background analysis outcomes
- docs and control-plane updates that explain the reliability boundary for the second Stage H wave

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests`
- `npm --prefix web run verify`
- `git diff --check`

## Completion Criteria

- the second Stage H wave ends with replayable or regression-friendly review instead of only manual inspection
- tool-aware Research analysis remains honest and explainable as capability depth increases
