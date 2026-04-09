# Stage J-05: Auth, Observability, and Learning Closeout

## Why

A fuller MCP learning stage is incomplete unless auth, transport, and degraded behavior stay visible enough to inspect
and explain.

## Scope

- extend trace and review for the fuller MCP path
- make auth failures and transport failures distinguishable
- make resource-versus-tool usage distinguishable
- make prompt usage distinguishable when it is present
- close out Stage J with a short learning summary and operator-facing review baseline

## Non-Goals

- generic audit redesign
- cross-module rollout beyond Research

## Deliverables

- one MCP-aware review baseline covering resource, tool, auth, and transport outcomes
- one operator-facing surface that keeps those outcomes readable
- one learning closeout that explains the MCP path in `AI 前沿研究` terms instead of in generic Research terms
- one Stage J closeout-ready documentation update

## Verification

- backend tests
- frontend verify
- `git diff --check`

## Completion Criteria

- the MCP learning path is reviewable enough that the project can move on without hiding core protocol behavior
