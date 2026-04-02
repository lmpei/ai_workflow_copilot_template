# Stage I-09: Control-Plane Roadmap Alignment Clarity

## Why

Recent discussion showed that the control-plane docs made it too easy to confuse completed bounded task waves with
exhaustive roadmap-wave completion, especially around Stage I and the broader Wave 2 MCP questions.

## Scope

- clarify the distinction between bounded `STAGE_*_PLAN` execution units and broader roadmap capability waves
- make Stage I versus Wave 2 status readable without changing product scope
- keep the cleanup bounded to control-plane and planning docs

## Non-Goals

- new connector or MCP code
- stage-direction changes without explicit documentation
- architecture or deployment rewrites

## Deliverables

- one clearer control-plane explanation of bounded stage versus roadmap wave
- one aligned Stage I plan and roadmap description
- one append-only decision entry and status update

## Verification

- docs consistency review
- `git diff --check`

## Completion Criteria

- readers can tell the difference between Stage I closeout and broader Wave 2 concept coverage
- the docs state explicitly whether Wave 2 minimum exit signal is already met
- the remaining MCP-specific gap is described as optional follow-through instead of as hidden ambiguity
