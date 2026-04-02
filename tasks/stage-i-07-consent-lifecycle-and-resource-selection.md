# Stage I-07: Consent Lifecycle and Resource Selection

## Why

Once external context becomes a more explicit resource, the product should stop treating consent as a one-time hidden
grant. The bounded pilot should show where consent changes and explicit resource selection live on the Research surface.

## Scope

- add bounded consent lifecycle behavior such as clearer current state and revocation or reset semantics
- let the Research path explicitly choose from recent approved external resource snapshots where appropriate
- keep the workflow honest when consent is withdrawn or no usable resource is selected

## Non-Goals

- organization-wide permission systems
- generic connector administration UI
- cross-module rollout

## Deliverables

- one clearer consent lifecycle contract for the bounded Research connector pilot
- one explicit resource-selection step or surface on the Research path
- docs and control-plane updates

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests`
- `npm --prefix web run verify`
- `git diff --check`

## Completion Criteria

- users and operators can tell whether the connector is still authorized
- the Research path can explicitly select from the bounded external resource snapshots instead of only auto-blending
- revoked or unavailable consent leads to honest degraded behavior
