# Stage I-03: Research External Context Pilot

## Why

After the connector contract exists, the repository should prove one bounded external-context path on the main Research
surface instead of broadening to multiple integrations.

## Scope

- connect one external context source to one Research workflow
- keep the pilot visibly distinct from ordinary internal retrieval
- preserve honest degraded behavior when the external source is unavailable or denied

## Non-Goals

- connector marketplace behavior
- multi-module connector rollout
- connector-driven autonomous actions

## Deliverables

- one Research-first external-context pilot
- one visible product path that uses the connector when permitted
- one honest degraded path when the connector is denied, unavailable, or returns no useful context
- docs and control-plane updates

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests`
- `npm --prefix web run verify`
- `git diff --check`

## Completion Criteria

- one Research path can use approved external context
- users and operators can still distinguish internal retrieval from connector-backed context
