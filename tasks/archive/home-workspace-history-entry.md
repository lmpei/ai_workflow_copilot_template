# Home Workspace History Entry

## Goal

Restore a clear, lightweight homepage entry to the full workspace history page so users can always find past workspaces
from the first screen.

## Scope

- add one visible homepage link to `/workspaces`
- keep the homepage visual hierarchy light instead of reintroducing a large history block

## Non-Goals

- redesign the workspace history page
- bring the old homepage history block back

## Verification

- `npm --prefix web run verify`
- `git diff --check`
