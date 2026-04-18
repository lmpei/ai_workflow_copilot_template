# Task: AI Frontier Workbench Simplification

## Goal

Make the `AI 前沿研究` workbench lighter by removing repeated or overly technical surfaces from the main user path.

## Scope

- simplify the visible research workbench into one single-column flow
- remove the right-side rail from the research workbench
- remove the main-entry exposure of trace/readiness and separate "formal output" actions
- stop exposing analysis mode switching to ordinary users
- keep the user path centered on:
  - source intake
  - one current research result
  - recent research records

## Non-Goals

- no MCP protocol changes
- no Support or Job workflow redesign
- no operator/debug surface removal from the codebase

## Expected Outcome

- the research workbench no longer looks like a technical shell
- the default user path is lighter and easier to understand
- technical process details remain available only outside the main user path

## Verification

- `npm --prefix web run verify`
- review the control-plane docs for consistency
