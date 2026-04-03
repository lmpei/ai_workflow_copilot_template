# Stage I-16: Research Remote MCP Resource Pilot

## Why

Once the repo can act as a real MCP client, the visible Research path should stop depending on the local in-process
shortcut and should prove one bounded out-of-process MCP resource flow on the main product surface.

## Scope

- connect `research_external_context` to one bounded out-of-process MCP resource
- preserve the same consent and snapshot reuse boundaries
- keep internal workspace evidence and remote MCP context visibly distinct

## Non-Goals

- multiple remote MCP resources
- broad connector marketplace behavior
- replacing the existing snapshot model

## Deliverables

- one visible Research path that reads one remote MCP resource
- honest degraded behavior when transport or resource access fails
- snapshot reuse still available as an explicit alternative path

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests`
- `npm --prefix web run verify`
- `git diff --check`

## Completion Criteria

- Research can use one out-of-process MCP-backed context source on the main product path
- denied, unavailable, and empty-resource cases remain honest
- snapshot reuse still works without forcing the remote MCP read every time
