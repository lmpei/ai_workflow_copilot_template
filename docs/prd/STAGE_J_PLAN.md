# Stage J Plan

## Stage Name

`Stage J: Complete MCP Understanding and Independent Server Integration`

## Status

- Status: complete and closed
- Opened At: 2026-04-08
- First Task Wave: complete

## Position In The Project

Stage J begins after the closeout of Stage I. Stage I already delivered one bounded connector-backed MCP baseline on
the current product hosts. Stage J changed the learning style: instead of adding another narrow MCP follow-through
inside the same repo-local pilot shape, it built one more complete MCP understanding path around one independent MCP
server and one fuller product-side integration.

## Roadmap Alignment

- Roadmap theme:
  - `Theme 3: Staged AI Capability Expansion`
- Roadmap wave:
  - `Wave 2: Connector and Context Plane`
- Stage-J interpretation:
  - this plan defined one complete MCP-learning execution unit, not just one more bounded Stage I follow-through
- Wave interpretation:
  - Wave 2 remains the broader concept family; Stage J covered MCP more coherently, but still did not require
    exhaustive platform breadth across every host or module

## Stage Goal

Gain a fuller working understanding of MCP by building one independent MCP server outside this repository and one
product-visible integration path for `AI 前沿研究` that covers resources, tools, prompts, auth, transport, and review
coherently enough to teach the protocol rather than only demonstrate fragments of it.

## Primary Outcome

The repository gained:

- one clear capability map for MCP roles and surfaces
- one independent MCP server boundary outside this repo
- one product-visible MCP resource path and one product-visible MCP tool path
- one explicit auth, transport, trace, and review baseline around that fuller MCP path

## Capability Contract

Stage J treated the following as fixed:

- product host:
  - this repo owns the visible workflow, consent boundary, review, and degraded behavior
- MCP client:
  - this repo owns the MCP client and transport integration
- independent MCP server:
  - a separate repo or working directory outside this repository owns the server implementation
- first resource:
  - `ai.frontier.digest`
- first tool:
  - `ai.frontier.search`
- first prompt:
  - `ai.frontier.brief`
- first transport:
  - `stdio`
- first auth model:
  - one bearer-style token contract

The detailed contract of record is:

- `docs/prd/MCP_CAPABILITY_MAP.md`

## Non-Goals

Stage J did not primarily optimize for:

- broad multi-server MCP marketplace UX
- multi-agent orchestration
- cross-module MCP rollout across Support and Job
- realtime or multimodal work

## Success Criteria

Stage J is successful when:

- the owner can point to one independent MCP server outside this repo and explain how the product acts as an MCP client
- the owner can explain the difference between MCP resources, tools, and prompts through code that exists in the
  system rather than only through theory
- the visible product path uses at least one MCP resource and one MCP tool behind explicit auth and review boundaries
- the visible product path clearly serves `AI 前沿研究` instead of the older generic Research definition
- trace and review make transport, auth, endpoint identity, and degraded behavior readable enough for learning and demo

## First Task Wave

The first executable Stage J wave was:

1. `tasks/archive/stage-j/stage-j-02-mcp-capability-map-and-independent-server-contract.md`
2. `tasks/archive/stage-j/stage-j-03-independent-mcp-server-repo-bootstrap.md`
3. `tasks/archive/stage-j/stage-j-04-product-resource-tool-prompt-integration.md`
4. `tasks/archive/stage-j/stage-j-05-auth-observability-and-learning-closeout.md`

## Closeout Summary

- complete: `stage-j-02`, which fixed the Stage J MCP capability map and the boundary between this repo and the new independent MCP server repo
- complete: `stage-j-03`, which bootstrapped the independent MCP server at `D:\ai-try\weave-mcp-server`
- complete: `stage-j-04`, which moved the visible `AI 前沿研究` path onto MCP resource, tool, and prompt usage
- complete: `stage-j-05`, which made MCP tool identity, prompt identity, auth outcome, transport outcome, and degraded behavior reviewable enough for operator learning

Stage J is now complete and closed.

The learning closeout of record is:

- `docs/prd/STAGE_J_MCP_LEARNING_SUMMARY.md`
