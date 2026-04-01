# Stage H-07: Research Background Analysis Runs

## Why

The first Research tool-assisted pilot still behaves like a synchronous chat turn. The next bounded learning step in
the roadmap is to understand when visible Research analysis should become a background-capable run instead of a single
request/response exchange.

## Scope

- add one bounded background-capable Research analysis run path on top of the existing tool-assisted pilot
- keep the user-facing Research workbench understandable while analysis continues beyond a single chat response
- preserve honest degraded behavior and trace visibility instead of hiding long-running work behind generic loading
  states

## Non-Goals

- connector or MCP integration
- multi-agent handoffs or planner/worker orchestration
- broad rollout into Support or Job

## Deliverables

- one visible Research analysis run concept that can progress beyond a single chat turn
- one user-facing status path for pending, running, completed, or degraded analysis runs
- docs and control-plane updates that explain the bounded background-execution rule

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests`
- `npm --prefix web run verify`
- `git diff --check`

## Completion Criteria

- one Research-first analysis path can continue as an explicit run instead of only as a synchronous response
- the product can show analysis-run state honestly without pretending to implement a full orchestration system
