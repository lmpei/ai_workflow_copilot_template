# Stage K-04: Frontier Summary Judgment And Project Card Outputs

## Goal

Replace the older generic Research output shape with one output contract that matches `AI 前沿研究`.

## Scope

- define one stable output contract for:
  - frontier summary
  - trend judgment
  - project cards
  - reference sources
- ensure project cards can carry accurate official links distinctly from the main prose
- keep sources separated from the main narrative instead of mixing long link lists into the answer body

## Out Of Scope

- broad visual redesign
- Support or Job changes

## Deliverables

- backend output contract updates
- frontend rendering support for summary, judgment, project cards, and reference links
- one clear rule that source lists live separately from the main written analysis

## Verification

- backend tests if output contracts change
- `npm --prefix web run verify`
