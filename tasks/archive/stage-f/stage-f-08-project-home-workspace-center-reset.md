# Task: stage-f-08-project-home-workspace-center-reset

## Goal

Turn the project-facing home into a lighter workspace center with one lightweight guided-demo entry and one bounded
continuation area for existing workspaces.

## Project Stage

- Stage: Stage F
- Track: Delivery and Operations with Research and Platform Reliability support

## Why

Once the root home page and product entry are separated, the project home should stop trying to educate the user about
everything at once. It should simply help the user start a guided demo, continue an existing workspace, or create a
new one.

## Context

Relevant documents:

- `docs/prd/STAGE_F_PLAN.md`
- `tasks/stage-f-07-personal-homepage-and-project-entry-split.md`
- `STATUS.md`

## Scope

Allowed work:

- reduce the project-facing home to a compact workspace center
- keep one lightweight guided-demo entry
- put existing workspaces inside one fixed-height scroll region
- keep a simple new-workspace action without making it the main visual focus

Disallowed work:

- rebuilding the inside of the workspace workbench
- turning the project home into another long-form explanation page

## Acceptance Criteria

- the project-facing home behaves like a workspace center rather than a second marketing page
- existing workspaces do not expand the page without bound
- guided demo entry remains visible but lightweight
- a returning user can quickly continue work without parsing heavy explanatory content
