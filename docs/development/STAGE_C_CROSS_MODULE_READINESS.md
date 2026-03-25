# Stage C Cross-Module Readiness

This document defines the minimum shared readiness path for Research, Support, and Job during Stage C.

It does not introduce production-grade release governance. It defines the smallest repeatable way to verify that a
candidate is demo-ready across all three scenario modules without relying on hidden project knowledge.

## Readiness Goal

A Stage C candidate is considered cross-module ready when a collaborator can verify:

- Research, Support, and Job each have a visible workflow entry point
- each module can produce either a grounded result or an explicit degraded result
- module eval expectations are visible and tied back to the scenario registry baseline
- the rehearsal evidence and handoff note say which module surfaces were checked

## Shared Candidate Checklist

Every Stage C candidate should satisfy these checks:

1. login succeeds and the workspace list loads
2. at least one workspace for each module surface is available or intentionally documented as unavailable
3. each module workspace loads its documents, tasks, and eval surfaces without hidden setup
4. each module can run its default workflow task or show an honest degraded result when context is thin
5. the eval surface shows the module quality baseline and pass threshold for the candidate being reviewed
6. the release evidence and handoff note explicitly name which module surfaces were checked

## Module Workflow Checks

### Research Assistant

- run either `research_summary` or `workspace_report`
- confirm the output includes structured sections and evidence references, or an explicit `no_documents` style result
- confirm traces or task history remain visible after the run

### Support Copilot

- run either `ticket_summary` or `reply_draft`
- confirm the output includes `case_brief`, `triage`, and `next_steps`
- if the workspace lacks support context, confirm the result escalates honestly instead of implying a grounded fix

### Job Assistant

- run either `jd_summary` or `resume_match`
- confirm the output includes `review_brief`, `assessment`, and `next_steps`
- if the workspace lacks hiring context, confirm the result surfaces gaps and missing materials instead of implying a grounded hiring decision

## Eval Baseline Checks

For each module candidate under review:

- the eval surface should show the module quality baseline from the scenario registry
- the eval surface should show the pass threshold from the scenario registry
- there should be either:
  - a current eval dataset or run for the module's default eval task
  - or a documented note explaining why eval coverage is still pending

Recommended Stage C default eval focus:

- Research: `research_summary`
- Support: `reply_draft`
- Job: `resume_match`

## Honest Degraded Output Rule

Cross-module readiness requires honest degraded outputs.

If context is thin, missing, or not strongly grounded:

- Research should expose evidence gaps rather than pretend synthesis confidence
- Support should expose missing knowledge and escalation needs rather than pretend a grounded fix exists
- Job should expose missing materials or weak fit evidence rather than pretend a grounded hiring decision exists

## Rehearsal Evidence Rule

Every Stage C demo or release-like rehearsal should record:

- which Research workspace or task was checked
- which Support workspace or task was checked
- which Job workspace or task was checked
- whether each module showed a grounded or degraded result
- which eval datasets or runs were inspected
- which module surfaces remain out of scope or still need follow-up

## Related Docs

- `docs/development/DELIVERY_BASELINE.md`
- `docs/development/STAGING_RELEASE_PATH.md`
- `docs/prd/STAGE_C_PLAN.md`
- `docs/PROJECT_GUIDE.md`

