# Stage H-04: Tool Trace and Eval Visibility

## Why

The first capability wave should not ship as a black box. If tool-assisted behavior lands, traces and eval-facing
surfaces must show what happened, where degradation occurred, and how the output should be interpreted.

## Scope

- expose the first Stage H tool behavior in traces or closely related inspection surfaces
- add the minimum eval-facing or regression-facing visibility needed for honest review
- preserve degraded-output honesty instead of collapsing everything into generic success summaries

## Non-Goals

- a full new observability platform
- cross-module grading unification
- broad quality-dashboard redesign

## Deliverables

- trace-visible tool behavior for the Stage H pilot
- one bounded eval or regression baseline that covers the pilot
- updated docs that explain the honest-visibility rule

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests`
- `npm --prefix web run verify`
- `git diff --check`

## Completion Criteria

- the Stage H pilot is observable enough to support honest debugging and future capability waves
- tool use and degraded paths are visible rather than hidden behind generic outputs
