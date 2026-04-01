# Stage H-02: Responses-Style Model Interface Foundation

## Why

The current provider integration is good enough for the existing demo, but the next capability wave needs a clearer
model-facing contract before any tool-assisted path can become durable. The repository should modernize that contract in
one shared place instead of scattering provider-specific behavior across module flows.

## Scope

- define one shared model-interface layer that can express modern request and response behavior
- adapt the current provider path behind that layer without breaking the existing public product hosts
- preserve current structured-output and module-contract expectations where they already exist
- update traces or stored metadata only where the new shared contract requires it

## Non-Goals

- shipping a broad multi-module tool-assisted rollout
- introducing MCP or external connector surfaces
- redesigning the front-end workflow
- replacing the shared runtime with provider-specific silos

## Deliverables

- one shared model-interface contract in the backend
- one provider-backed implementation path behind that contract
- docs and control-plane updates that explain the new foundation

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests`
- `npm --prefix web run verify`
- `git diff --check`

## Completion Criteria

- the repo has one shared modern model-interface foundation
- existing product hosts still run without deployment-boundary regressions
- the next Stage H pilot can build on the new contract instead of on ad hoc provider calls
