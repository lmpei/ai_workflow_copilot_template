# Status

Current state only. Keep this file short, current, and action-oriented.

## Metadata

- Last Updated: 2026-03-26

## Project Mode

- Execution

## Current Phase

- Phase 5 baseline complete
- Stage A complete and closed
- Stage B complete and closed
- Stage C complete and closed
- Stage D active with second task wave active

## Current Objective

- execute the second bounded Stage D wave so the public-demo baseline can turn into a real internet-accessible rollout path

## Active Task

- `tasks/stage-d-07-public-demo-deployment-path-and-env-wiring.md`

## Verification Status

- Summary: Stage D wave one already established guardrails, guided showcase paths, and a bounded operator routine; wave two now has a fixed first deployment target and moves next into repo-side deployment wiring.
- Last Verified At: 2026-03-26

## Current Blockers

- none

## Assumptions

- module product names remain unchanged for now
- Research remains the reference workflow for deeper demo-path storytelling
- public-demo work stays bounded and does not drift into full production SaaS claims

## Information Gaps

- which repo-side deployment wiring changes are strictly necessary for the chosen single-VM rollout shape, and which can stay outside the repo for now

## Ready Now

1. execute `tasks/stage-d-07-public-demo-deployment-path-and-env-wiring.md`
2. keep the deployment path aligned with the single-VM Compose-style contract fixed in `stage-d-06`
3. preserve the current public-demo showcase and operator path as the baseline while rollout work proceeds

## Parked / Later

1. deeper non-Research workbench layers after the public-demo baseline is stable
2. staged AI capability expansion from `docs/prd/LONG_TERM_ROADMAP.md`
3. product-name redesign for the three scenario modules

## Last Completed Task

- `tasks/archive/stage-d/stage-d-06-public-hosting-target-and-deployment-contract.md`

## Recent Decisions

- `DEC-2026-03-18-007` close Stage A as complete
- `DEC-2026-03-18-008` define Stage B as the next formal planning unit
- `DEC-2026-03-21-018` complete `stage-b-08` by pairing the Stage B rehearsal path with release evidence records and reusable evidence templates
- `DEC-2026-03-21-019` close Stage B as complete
- `DEC-2026-03-21-020` define Stage C as the next formal planning unit
- `DEC-2026-03-21-021` use `stage-c-*` naming for Stage C tasks
- `DEC-2026-03-21-022` define the first Stage C task wave as `stage-c-02`, `stage-c-03`, and `stage-c-04`
- `DEC-2026-03-22-023` define the global governance baseline initiated during Stage C early execution and execute it through `stage-c-06` through `stage-c-09`
- `DEC-2026-03-22-024` canonicalize module contracts and lifecycle terminology across backend and frontend
- `DEC-2026-03-22-025` complete `stage-c-06` and move the active governance step to `stage-c-07`
- `DEC-2026-03-22-026` complete `stage-c-07`, make `server/app/schemas/scenario.py` the canonical scenario registry, and move the active governance step to `stage-c-08`
- `DEC-2026-03-22-027` complete `stage-c-08`, centralize runtime-control transitions, move Research task execution into an explicit extension, and move the active governance step to `stage-c-09`
- `DEC-2026-03-22-028` complete `stage-c-09`, close the global governance baseline, and return the active Stage C task to `stage-c-02`
- `DEC-2026-03-23-029` complete `stage-c-10`, repair backend CI typing/lint drift, and keep the active Stage C execution task on `stage-c-02`
- `DEC-2026-03-25-030` complete `stage-c-02`, deepen Support Copilot into a structured grounded case workflow, and move the active Stage C task to `stage-c-03`
- `DEC-2026-03-25-031` complete `stage-c-03`, deepen Job Assistant into a structured hiring workflow, and move the active Stage C task to `stage-c-04`
- `DEC-2026-03-25-032` complete `stage-c-04`, define the lightweight cross-module readiness baseline, and close the first Stage C task wave
- `DEC-2026-03-25-033` define the second Stage C task wave as `stage-c-12`, `stage-c-13`, and `stage-c-14`, with `stage-c-12` as the next active task
- `DEC-2026-03-25-034` complete `stage-c-12`, deepen Support Copilot into a follow-up and escalation workflow, and move the active Stage C task to `stage-c-13`
- `DEC-2026-03-26-035` complete `stage-c-13`, deepen Job Assistant into shortlist and candidate-comparison workflow depth, and move the active Stage C task to `stage-c-14`
- `DEC-2026-03-26-036` complete `stage-c-14`, make cross-module eval coverage and rehearsal evidence more durable, and close the second Stage C task wave
- `DEC-2026-03-26-037` close Stage C as complete instead of extending it into the public-demo and future-capability roadmap
- `DEC-2026-03-26-038` create `docs/prd/LONG_TERM_ROADMAP.md` to hold the multi-stage learning and capability direction after Stage C
- `DEC-2026-03-26-039` define `Stage D` as `Public Internet Demo Baseline` and open the first Stage D task wave with `stage-d-02` through `stage-d-04`
- `DEC-2026-03-26-040` clarify the AI capability roadmap into explicit adoption waves while keeping that roadmap separate from the bounded Stage D plan
- `DEC-2026-03-26-041` complete `stage-d-02`, add explicit public-demo guardrails and a `/api/v1/public-demo` settings surface, and move the active Stage D task to `stage-d-03`
- `DEC-2026-03-26-042` complete `stage-d-03`, add backend-owned guided demo templates plus seeded workspace creation and showcase-path UI, and move the active Stage D task to `stage-d-04`
- `DEC-2026-03-26-043` complete `stage-d-04`, add bounded public-demo smoke and refresh scripts plus an operator runbook, and leave the next Stage D direction open for human confirmation
- `DEC-2026-03-26-044` define the second Stage D wave as `stage-d-06`, `stage-d-07`, and `stage-d-08`, with `stage-d-06` as the next active task
- `DEC-2026-03-26-045` complete `stage-d-06`, choose a single public Linux VM plus Docker Compose-style stack as the first hosting target, and move the active Stage D task to `stage-d-07`