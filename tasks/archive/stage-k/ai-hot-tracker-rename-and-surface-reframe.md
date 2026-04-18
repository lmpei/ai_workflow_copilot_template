# Task: AI Hot Tracker Rename And Surface Reframe

## Goal

Replace the visible `AI 前沿研究` product framing with `AI 热点追踪`, and redesign the product home plus the module workbench so the surface feels like a real product instead of a technical shell.

## Scope

- rename the visible Research module product name to `AI 热点追踪`
- use one English subtitle for the module where needed
- redesign the app home so it feels like a real product entry surface
- redesign the research workbench into one custom module surface instead of reusing the older generic template feel
- remove older visible `Research` wording from quick-start and main product entry surfaces

## Non-Goals

- no backend module_type rename
- no MCP protocol redesign
- no Support or Job workflow redesign beyond visible naming consistency

## Expected Outcome

- the product home looks intentional and product-like
- `AI 热点追踪` reads like a distinct module, not a leftover Research shell
- quick-start and module entry language no longer expose the older Research label

## Verification

- `npm --prefix web run verify`
- update control-plane docs for the renamed visible module contract
