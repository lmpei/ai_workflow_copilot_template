# Stage I-11: MCP Contract and Local Server Foundation

## Why

Stage I currently has a connector-backed baseline, but no actual MCP contract exists in the repo. The next bounded step
should add the minimum MCP-facing foundation without broadening into a generic connector platform.

## Scope

- define one minimal MCP-facing contract in the backend
- add one local MCP server foundation for bounded Research-first use
- keep consent and permission boundaries aligned with the existing Stage I connector model

## Non-Goals

- a full MCP marketplace
- multiple MCP servers
- broad front-end management surfaces

## Deliverables

- one minimal MCP contract and server foundation
- one Research-first permission boundary for that MCP path
- docs and control-plane updates

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests`
- `npm --prefix web run verify`
- `git diff --check`

## Completion Criteria

- the repo has one bounded MCP server or resource contract instead of only generic connector language
- the MCP path is still Research-first and permission-aware
- later Stage I tasks can build a real Research MCP pilot on top of it
