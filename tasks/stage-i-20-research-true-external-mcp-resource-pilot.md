# Stage I-20: Research True External MCP Resource Pilot

## Why

Once the repo can reach one true external MCP endpoint, the visible Research path should prove one bounded off-repo
MCP resource flow instead of stopping at the repo-local subprocess server.

## Scope

- connect `research_external_context` to one bounded true external MCP resource
- preserve consent, snapshot reuse, and honest degraded behavior
- keep internal workspace evidence and external MCP context visibly distinct

## Non-Goals

- multiple external MCP resources
- broad connector marketplace behavior
- replacing the existing snapshot model

## Deliverables

- one visible Research path that reads one true external MCP resource
- honest degraded behavior when endpoint, transport, or resource access fails
- snapshot reuse still available as an explicit alternative path

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests`
- `npm --prefix web run verify`
- `git diff --check`

## Completion Criteria

- Research can use one true external MCP-backed context source on the main product path
- denied, unavailable, auth-failed, and empty-resource cases remain honest
- snapshot reuse still works without forcing the external MCP read every time
