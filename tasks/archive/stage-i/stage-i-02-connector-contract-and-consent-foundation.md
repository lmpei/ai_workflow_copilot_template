# Stage I-02: Connector Contract and Consent Foundation

## Why

Before any external context pilot goes live, the repository needs one explicit connector contract and one bounded
consent model instead of ad hoc external calls.

## Scope

- define one shared connector or external-context contract in the backend
- add one bounded consent or permission record for that contract
- keep the initial contract narrow enough for one Research-first pilot

## Non-Goals

- multiple connectors
- broad module rollout
- deep UI productization of connector management

## Deliverables

- one backend connector contract
- one bounded consent or permission persistence layer
- one API surface for checking or granting the pilot permission boundary
- docs and control-plane updates

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests`
- `npm --prefix web run verify`
- `git diff --check`

## Completion Criteria

- the repo has one stable connector contract instead of implicit external calls
- the external-context pilot can only run behind one explicit permission or consent boundary
