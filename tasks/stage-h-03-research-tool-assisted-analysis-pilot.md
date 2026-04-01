# Stage H-03: Research Tool-Assisted Analysis Pilot

## Why

Stage H needs one visible capability pilot, but it should stay bounded. Research remains the reference workflow, so the
first tool-assisted path should land there before any broader rollout reaches Support or Job.

## Scope

- choose one bounded Research path that uses the new model-interface foundation
- make that path visible enough to demonstrate modern tool-assisted analysis behavior
- keep the pilot aligned with the existing Research workbench instead of creating a separate experimental surface

## Non-Goals

- broad multi-module rollout
- connector marketplace work
- realtime, multimodal, or multi-agent orchestration

## Deliverables

- one Research-first capability pilot built on the Stage H interface foundation
- one product-visible path that distinguishes the pilot from ordinary grounded interaction

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests`
- `npm --prefix web run verify`
- `git diff --check`

## Completion Criteria

- one bounded Research path can demonstrate tool-assisted analysis on the live product surface
- the pilot remains understandable and does not destabilize the rest of the product
