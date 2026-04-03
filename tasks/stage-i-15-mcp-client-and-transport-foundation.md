# Stage I-15: MCP Client and Transport Foundation

## Why

The repo now has a bounded local MCP server and one visible MCP-backed Research path, but it still does not act as a
true MCP client against a separate server process.

## Scope

- add one bounded out-of-process MCP client path
- define one transport-aware MCP server configuration contract
- reuse the existing Research-first consent boundary

## Non-Goals

- multiple MCP servers at once
- broad connector UI redesign
- multi-module rollout

## Deliverables

- one MCP client foundation that talks to a separate MCP server process
- one bounded config or registry contract for that server
- one Research-first permission gate that still reuses workspace consent

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests`
- `npm --prefix web run verify`
- `git diff --check`

## Completion Criteria

- the repo can read one MCP resource through a real out-of-process client path
- the new path stays behind the same Research-first consent boundary
- the repo no longer relies only on direct in-process MCP imports for its MCP baseline
