# Stage I-19: Connector-Configured Remote MCP Endpoint Foundation

## Why

The repo can now talk to one repo-local out-of-process MCP server, but it still cannot describe or reach one true
external MCP endpoint outside this repository.

## Scope

- add one bounded remote MCP endpoint contract behind the existing Research connector boundary
- define how one connector can describe one true external MCP server and one bounded resource target
- preserve the current workspace consent gate before any remote read occurs

## Non-Goals

- multiple remote MCP endpoints at once
- broad connector configuration UI
- full secret-management redesign

## Deliverables

- one bounded connector-aware remote MCP endpoint contract
- one read or describe path that can target one true external MCP endpoint
- one health or validation surface for that bounded endpoint

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests`
- `npm --prefix web run verify`
- `git diff --check`

## Completion Criteria

- the repo can describe and read one bounded MCP resource from one configured external endpoint
- the endpoint still sits behind the same Research-first connector consent boundary
- the repo no longer depends only on repo-local MCP server processes for its visible MCP path
