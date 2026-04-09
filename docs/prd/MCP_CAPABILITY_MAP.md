# MCP Capability Map

## Purpose

This document fixes one complete MCP learning target for Stage J so later work does not drift back into narrow
follow-through tasks without a full protocol model.

## Local Learning Goal

The project should be able to explain MCP through one running system that includes:

- one product host in this repository
- one MCP client in this repository
- one independent MCP server outside this repository
- one visible MCP resource path
- one visible MCP tool path
- one explicit MCP prompt example
- one explicit auth, transport, trace, and review baseline

## Roles In This Project

### Product Host

- repo: `D:\ai-try\ai_workflow_copilot_template`
- responsibility:
  - own the user-facing workflow
  - own workspace consent and operator review
  - decide when MCP should be read or invoked
  - render resource, tool, and degraded behavior visibly

### MCP Client

- repo: `D:\ai-try\ai_workflow_copilot_template`
- responsibility:
  - connect to the independent MCP server
  - authenticate
  - read resources
  - call tools
  - optionally request prompts
  - surface transport, auth, and failure signals

### Independent MCP Server

- repo or working directory target: `D:\ai-try\weave-mcp-server`
- responsibility:
  - expose one resource
  - expose one tool
  - expose one prompt
  - enforce one bounded auth contract
  - remain understandable enough for learning and debugging

## First Capability Set

### First Resource

- id: `ai.frontier.digest`
- shape:
  - one bounded AI-frontier context digest
  - optimized for reading, not action-taking
- purpose:
  - teach what an MCP resource is
  - provide read-only context for AI-frontier analysis

### First Tool

- id: `ai.frontier.search`
- shape:
  - one bounded search action over the same AI-frontier source domain
- purpose:
  - teach what an MCP tool is
  - show how tool use differs from resource reading

### First Prompt

- id: `ai.frontier.brief`
- shape:
  - one reusable MCP prompt that helps frame an AI-frontier research brief
- purpose:
  - teach what an MCP prompt is
  - give one explicit prompt example without turning prompts into a generic prompt-management project

## Boundary Between Repositories

### Product Repository

The product repo keeps:

- user-facing workflows
- connector consent lifecycle
- MCP client configuration
- trace and review visibility
- product-specific fallback and degraded behavior

The product repo does not keep:

- the long-term home of the independent MCP server
- MCP server-side business logic once Stage J bootstraps the independent server

### Independent MCP Server Repository

The independent MCP server keeps:

- server bootstrap and startup command
- resource implementation
- tool implementation
- prompt implementation
- server-side auth check
- server-side smoke validation

The independent MCP server does not keep:

- workspace state
- product review UI
- product consent records

## Transport Contract

Stage J starts with one transport only:

- `stdio`

Why:

- it is the smallest transport that still teaches a real client or server boundary
- it avoids hiding the protocol behind direct imports or in-process shortcuts

What is explicitly deferred:

- HTTP streaming transport
- multi-transport support
- discovery or marketplace layers

## Auth Contract

Stage J starts with one bounded auth model:

- bearer-style token passed from product client to independent MCP server

Why:

- it is enough to teach auth state, auth failure, missing credential behavior, and review visibility
- it keeps the learning path concrete without pretending the project already needs OAuth breadth

What is explicitly deferred:

- OAuth
- token refresh
- multi-tenant secret rotation

## Product-Side Learning Path

The product should end Stage J with:

1. one visible `AI 前沿研究` path that reads `ai.frontier.digest`
2. one visible `AI 前沿研究` path that invokes `ai.frontier.search`
3. one visible prompt-assisted path that uses `ai.frontier.brief`
4. one operator-facing review path that distinguishes:
   - resource use
   - tool use
   - prompt use
   - auth failure
   - transport failure
   - degraded fallback

## Stage J Interpretation

Stage J is not a generic MCP platform build-out.

Stage J is successful when the owner can explain, from running code:

- what MCP resources are
- what MCP tools are
- what MCP prompts are
- what the client does
- what the server does
- how auth and transport fit in
- how the product exposes all of that honestly
