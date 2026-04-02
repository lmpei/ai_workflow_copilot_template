# Stage I-12: Research MCP Resource Context Pilot

## Why

After the MCP foundation exists, the repo needs one visible product path that uses it. The pilot should stay narrow and
should reuse the existing Research consent, snapshot, and review boundaries instead of inventing a second context path.

## Scope

- connect one Research-first product path to one bounded MCP-backed resource source
- keep the pilot visible on the main Research surface
- preserve honest degraded behavior when MCP context is unavailable or denied

## Non-Goals

- multi-module MCP rollout
- generic MCP prompt or tool catalog management
- agent orchestration work

## Deliverables

- one visible Research MCP-backed context pilot
- one honest degraded path for denied, unavailable, or empty MCP context
- docs and control-plane updates

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests`
- `npm --prefix web run verify`
- `git diff --check`

## Completion Criteria

- a user-visible Research path can use one bounded MCP-backed source
- the product surface still distinguishes workspace evidence from MCP-backed context
- denied or unavailable MCP context remains honest and inspectable
