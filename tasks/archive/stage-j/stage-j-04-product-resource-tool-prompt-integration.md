# Stage J-04: Product Resource, Tool, and Prompt Integration

## Why

The product should not only read one MCP resource. It should show how a real MCP client uses resources, tools, and
prompts differently.

## Scope

- connect `ai.frontier.digest` into the visible `AI 前沿研究` path
- add one visible MCP tool path using `ai.frontier.search`
- add one bounded prompt usage path using `ai.frontier.brief`
- keep auth, degraded behavior, and trace visibility explicit

## Non-Goals

- broad multi-module rollout
- marketplace or discovery UX

## Deliverables

- one visible `AI 前沿研究` path that uses the Stage J MCP resource
- one visible `AI 前沿研究` path that uses the Stage J MCP tool
- one explicit prompt usage example that teaches prompt semantics without creating a generic prompt-management surface

## Verification

- backend tests
- frontend verify
- one end-to-end product-path check

## Completion Criteria

- the owner can explain the difference between MCP resources, tools, and prompts from the running product, not just from docs
