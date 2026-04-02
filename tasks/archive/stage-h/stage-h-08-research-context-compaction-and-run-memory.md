# Stage H-08: Research Context Compaction and Run Memory

## Why

Once Research analysis can outlive one chat turn, the repository needs one bounded answer for how conversation state,
tool results, and intermediate conclusions are compacted or resumed without losing user trust.

## Scope

- add one bounded compaction or memory strategy for Research analysis runs
- decide what analysis state stays user-visible versus operator-only
- keep the compaction layer traceable enough to support honest debugging and later eval work

## Non-Goals

- open-ended memory across every module
- fully automatic long-horizon autonomous research sessions
- connector-backed context planes

## Deliverables

- one bounded Research run-memory or compaction path
- one visible contract for how resumed analysis preserves key context
- docs and control-plane updates that explain the bounded compaction rule

## Verification

- `cd server && ..\\.venv\\Scripts\\python.exe -m pytest tests`
- `npm --prefix web run verify`
- `git diff --check`

## Completion Criteria

- the Research-first capability wave can resume or continue with bounded compaction instead of growing unbounded prompt
  state
- the new memory behavior is visible enough to inspect honestly in later trace and eval work
