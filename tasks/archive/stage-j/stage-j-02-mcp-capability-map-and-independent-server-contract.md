# Stage J-02: MCP Capability Map and Independent Server Contract

## Why

The next MCP step should not start by writing another partial server. It should start by fixing one complete learning
target in text.

## Scope

- define the exact MCP roles used in this project:
  - product host
  - MCP client
  - independent MCP server
- define what will be implemented as:
  - resources
  - tools
  - prompts
- define the repository boundary between this repo and the new independent MCP server repo
- define the auth and transport contract for the first independent MCP server

## Non-Goals

- coding the independent MCP server
- product-side MCP integration

## Deliverables

- one short MCP capability map in docs
- one agreed independent-server contract
- one agreed first resource, first tool, and first prompt for the learning path

## Verification

- docs consistency review
- `git diff --check`

## Completion Criteria

- the Stage J MCP target is complete enough that later implementation work no longer drifts into toy-minimum follow-through
