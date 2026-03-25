# Stage C Cross-Module Rehearsal Evidence Template

Copy this template outside git when you want a lightweight but durable Stage C rehearsal record.

Use it when the candidate is meant to demonstrate cross-module readiness across Research, Support, and Job rather than
only a generic Stage B staging restart path.

This template is intentionally lightweight. It records what was checked, what eval coverage exists, and which gaps
remain visible. It does not imply production-grade release governance.

## Evidence Metadata

- Completed At:
- Release Owner:
- Candidate Workspace or Demo Path:
- Env File:
- Change Ref:
- Rollback Target:
- Companion Handoff File:

## Cross-Module Coverage Snapshot

For each module, record:

- default eval task
- visible workspace or demo path
- whether default-task eval coverage is:
  - covered
  - template_only
  - missing
  - no_workspace
- known gap, if any

### Research Assistant

- Default eval task:
- Workspace checked:
- Coverage status:
- Quality baseline:
- Pass threshold:
- Known gap:

### Support Copilot

- Default eval task:
- Workspace checked:
- Coverage status:
- Quality baseline:
- Pass threshold:
- Known gap:

### Job Assistant

- Default eval task:
- Workspace checked:
- Coverage status:
- Quality baseline:
- Pass threshold:
- Known gap:

## Manual Module Checks

- [ ] login succeeds
- [ ] workspace navigation loads without hidden setup
- [ ] documents view loads
- [ ] Research shows either grounded output or an explicit degraded result
- [ ] Support shows either grounded output or an explicit degraded result
- [ ] Job shows either grounded output or an explicit degraded result
- [ ] eval coverage and pass-threshold expectations are visible for the reviewed candidate

## Eval Datasets / Runs Inspected

- Research:
- Support:
- Job:

## Honest Degraded Output Record

- Research gaps observed:
- Support gaps observed:
- Job gaps observed:

## Follow-up / Out of Scope

- Missing eval coverage still pending:
- Module surfaces intentionally not checked:
- Follow-up needed before wider use:
