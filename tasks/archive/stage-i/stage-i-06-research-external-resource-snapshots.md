# Stage I-06: Research External Resource Snapshots

## Why

The first external-context pilot can already blend approved external context into Research answers, but those external
matches still mostly live inside one answer or trace. The next bounded step should turn approved external matches into
explicit resource snapshots that can be inspected and reused.

## Scope

- persist bounded external-context matches as explicit resource-like snapshots on the Research path
- keep internal workspace evidence distinct from external resource snapshots
- expose those snapshots on the Research product surface and on analysis runs where needed

## Non-Goals

- broad multi-connector resource management
- full MCP resource protocol coverage
- Support or Job expansion

## Deliverables

- one persisted external-resource snapshot contract for the bounded Research connector path
- one operator- and user-visible surface where recent external resource snapshots can be inspected
- docs and control-plane updates

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests`
- `npm --prefix web run verify`
- `git diff --check`

## Completion Criteria

- approved external-context matches no longer exist only as transient answer-time data
- the Research pilot can show what external resource snapshot was actually used
- internal and external evidence remain visibly distinct
