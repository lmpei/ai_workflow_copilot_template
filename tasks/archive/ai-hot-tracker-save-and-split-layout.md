# AI Hot Tracker Save Chain And Split Layout

## Goal

Repair the `AI 热点追踪` save path, then rebuild the result page into one report-reading area plus one independent
follow-up module, and finally tighten report typography and layout so the surface reads like a product report instead of
field dumps.

## Scope

- fix the saved-record API chain so `保存` no longer fails with a backend `500`
- keep the current record/write API surface stable unless the fix requires a bounded contract correction
- rebuild the hot-tracker result page around:
  - left report area
  - right independent `追问` module
  - clear return entry
- keep `追问` as a report-bound chat surface, not as a generic assistant shell
- reduce internal field labels and explanation-style language on the user-facing surface
- improve typography, spacing, and hierarchy on the report body

## Non-Goals

- broad module rename work
- reopening the older generic workbench shell
- operator trace/review exposure on the user-facing surface
- changing the underlying hot-tracker report API route

## Requirements

### Save Chain

- clicking `保存` must succeed when the current report is valid
- saved records must tolerate empty or missing follow-up collections
- failures must surface as specific API errors instead of generic "API unreachable" when the backend is reachable

### Layout

- the page must no longer be "report + floating follow-up"
- the right `追问` area must be a dedicated page region with its own internal scroll
- the left report area must not be obscured by the right module
- the page must include a clear way to return to the previous surface

### Report Surface

- remove unnecessary field-label noise such as repeated internal section names
- present the report as a readable brief with stronger hierarchy and calmer density
- keep source links visible but subordinate to the report narrative

## Verification

- `cd server`
- `..\\.venv\\Scripts\\python.exe -m pytest tests`
- `npm --prefix web run verify`
- `git diff --check`
