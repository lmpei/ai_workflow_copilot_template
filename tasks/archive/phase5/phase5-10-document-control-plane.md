# Task: phase5-10-document-control-plane

## Goal

Introduce the top-level documentation control plane and align the repository so current state, stable facts, AI rules,
and execution tasks each have a clear home.

## Project Phase

- Phase: Phase 5
- Scenario module: shared platform core plus scenario modules

## Why

The repository has strong long-form docs and task history, but it needs a lighter control plane before the next
development stage is planned.

## Context

Relevant documents:

- `README.md`
- `AI_WORKFLOW.md`
- `AGENT_GUIDE.md`
- `docs/PROJECT_GUIDE.md`
- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`

## Flow Alignment

- Flow A / B / C / D: Flow A / B / C / D support docs only; no runtime behavior change
- Related APIs: none
- Related schema or storage changes: none

## Dependencies

- Prior task: `tasks/archive/phase5/phase5-09-runtime-structure-convergence.md`
- Blockers: none

## Scope

Allowed files:

- repository-root markdown control-plane docs
- `README.md`
- `AI_WORKFLOW.md`
- `AGENT_GUIDE.md`
- `docs/PROJECT_GUIDE.md`
- `tasks/README.md`
- `tasks/archive/phase5/phase5-10-document-control-plane.md`

Disallowed files:

- runtime code
- deployment files
- archived tasks except for references

## Deliverables

- Code changes:
  - none
- Test changes:
  - none
- Docs changes:
  - add `AGENTS.md`, `CONTEXT.md`, `STATUS.md`, `DECISIONS.md`, `ARCHITECTURE.md`
  - align `README.md`, `AI_WORKFLOW.md`, `AGENT_GUIDE.md`, and `docs/PROJECT_GUIDE.md`
  - add `tasks/README.md`

## Acceptance Criteria

- root control-plane docs exist and have distinct responsibilities
- `AGENTS.md` is the canonical AI rules file
- `README.md` points to the control plane instead of duplicating live state
- `STATUS.md` identifies the current objective and active task
- `DECISIONS.md` records the confirmed restructuring choices
- the existing `docs/` and `tasks/archive/` layers remain intact

## Verification Commands

- Repository:
  - `rg -n "AGENTS.md|CONTEXT.md|STATUS.md|DECISIONS.md|ARCHITECTURE.md" README.md AI_WORKFLOW.md docs/PROJECT_GUIDE.md prompts/CODING_AGENT_PROMPT_TEMPLATE.md tasks/README.md`
- Manual review:
  - check that `README.md`, `STATUS.md`, and `AGENTS.md` can orient a new collaborator without opening historical task files

## Tests

- Normal case
  - a collaborator can find the current state, stable facts, and AI rules from the top level
- Edge case
  - historical docs and archives remain usable without becoming the live state source
- Error case
  - the refactor must not create two conflicting AI-rules files or two conflicting live-status files

## Risks

- accidental duplication between new top-level docs and long-form docs
- stale references to `AGENT_GUIDE.md` as the canonical rules file

## Rollback Plan

- remove the added top-level control-plane docs
- restore README and project-guide links to the prior structure
- keep archived task history intact

## Final Results

- added the root control-plane docs: `AGENTS.md`, `CONTEXT.md`, `STATUS.md`, `DECISIONS.md`, and `ARCHITECTURE.md`
- added `tasks/README.md` and established the active-task versus archive-task workflow
- updated `README.md`, `AI_WORKFLOW.md`, `docs/PROJECT_GUIDE.md`, and the prompt template to use the new control-plane model
- converted `AGENT_GUIDE.md` into a compatibility pointer to `AGENTS.md`

## Execution Status

- Status: completed
- Verification:
  - repository consistency search completed
  - manual control-plane review completed
- Notes: this task is ready for archival under `tasks/archive/phase5/`
