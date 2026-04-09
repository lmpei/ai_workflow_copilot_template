# Stage J-03: Independent MCP Server Repo Bootstrap

## Why

MCP cannot be understood fully if the only server remains embedded in the product repository.

## Scope

- create the first independent MCP server boundary outside this repo
- create the first independent MCP server at `D:\ai-try\weave-mcp-server`
- implement:
  - resource `ai.frontier.digest`
  - tool `ai.frontier.search`
  - prompt `ai.frontier.brief`
- implement one bounded bearer-token auth contract for that server
- expose one documented startup command for local validation

## Non-Goals

- broad multi-resource server design
- third-party SaaS breadth

## Deliverables

- one independent MCP server repo or directory
- one working server startup path
- one resource, one tool, and one prompt exposed through MCP exactly as defined in `docs/prd/MCP_CAPABILITY_MAP.md`
- one auth path that the product repo can use

## Verification

- server-side MCP self-test or smoke validation
- documented startup command

## Completion Criteria

- the project no longer depends on repo-local MCP servers to explain MCP end to end
