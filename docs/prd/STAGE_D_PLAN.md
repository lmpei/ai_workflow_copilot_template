# Stage D Plan

## Stage Name

`Stage D: Public Internet Demo Baseline`

## Status

- Status: active
- Opened At: 2026-03-26
- First Task Wave: complete
- Second Task Wave: active

## Position In The Project

Stage D begins after the formal closeout of Stage C. Stage C proved that the shared platform can support deeper
non-Research workflows and a lightweight cross-module readiness routine. Stage D now narrows the next bounded stage to
one primary outcome: make the system publicly demoable on the internet without pretending it is already a
production-grade SaaS platform.

## Planning Model

Stage D operates under the same three-track roadmap model:

1. `Research`
2. `Platform Reliability`
3. `Delivery and Operations`

The tracks remain parallel, but Stage D changes the weighting. Delivery and Operations becomes the primary track
because public demo access is now the most important bounded goal.

## Priority Model

- Primary track:
  - `Delivery and Operations`
- Required parallel tracks:
  - `Platform Reliability`
  - `Research` as the reference workflow surface used to keep demo depth honest

Stage D should not optimize for more module features if those features delay a real public demo baseline.

## Stage Goal

Turn the repository from a mostly local or staging-oriented system into a real public internet demo that outside users
can log into and explore with bounded expectations, sample content, and basic operator guardrails.

## Track 1: Research

### Objective

Keep one clearly understandable workflow path visible so the public demo teaches how the platform works instead of only
showing infrastructure plumbing.

### Focus Areas

- backend-owned guided demo templates and seeded showcase paths across Research, Support, and Job
- one stable module-reference path that remains deep enough to demonstrate real workflow value
- honest public-facing explanation of what is grounded, what is degraded, and what remains demo-only

### Expected Outcomes

- a new user can reach a meaningful workflow quickly after login
- the public demo still reflects the repository's actual workflow depth instead of a hollow shell
- Stage D does not sacrifice learning value while improving access

## Track 2: Platform Reliability

### Objective

Add the minimum reliability guardrails required for public access.

### Focus Areas

- bounded signup and session handling expectations
- basic rate, quota, or abuse guardrails
- clearer public-facing error behavior
- enough operator visibility to diagnose demo failures quickly
- persistence and data-handling rules that are safe for a public demo baseline

### Expected Outcomes

- a public demo user cannot accidentally or cheaply destabilize the whole environment
- failures are easier to understand from the operator side
- the public demo stays honest about limits instead of silently degrading into confusion

## Track 3: Delivery and Operations

### Objective

Create a repeatable public-demo delivery path rather than keeping the system trapped in local-only development.

### Focus Areas

- public hosting target and environment shape
- demo-safe deploy and rollback routine
- seeded content or sample workspace preparation
- public demo operator checklist
- baseline runbook for keeping the public demo usable

### Expected Outcomes

- the project has one publicly reachable demo environment
- a collaborator can log in and follow a bounded showcase path without hidden setup
- the operator has a documented path for restart, rollback, and demo refresh

## Non-Goals

Stage D does not primarily optimize for:

- full production-grade SaaS hardening
- enterprise auth, billing, or organization management
- deep Support or Job workbench productization
- major new AI capability integrations beyond the minimum hooks needed to support the public demo path
- renaming the three module products

## Execution Rules

- Stage D tasks should use `stage-d-*` naming
- public-demo work should stay honest about demo limits and should not imply stronger production guarantees than exist
- sample or seeded content should clarify that it exists for demonstration and learning
- Stage D should favor access, clarity, and operator control over breadth of new feature work

## Success Criteria

Stage D is successful when:

- the system is reachable through a public internet URL
- a user can create an account and log into the public demo through the intended path
- at least one seeded or documented demo route exercises the existing workflow surfaces without hidden setup
- the operator has a bounded routine for deploy, restart, rollback, and demo refresh
- the repository is ready to shift the next stage toward Support and Job workbench productization

## Current Result

The first Stage D wave now provides:

- explicit public-demo guardrails and user-visible limits
- backend-owned guided demo templates for Research, Support, and Job
- seeded demo workspace creation through the real ingest path
- workspace-level showcase guidance for first-time collaborators
- a bounded public-demo operator runbook with smoke and refresh scripts

The second Stage D wave now has one fixed deployment contract:

- the first public target is one small Linux VM running the existing Docker Compose-style stack
- public access is split between `app.<domain>` and `api.<domain>`
- the repo keeps the internal `server`, `worker`, `db`, `redis`, and `chroma` shape instead of rewriting for a new platform first

## Next Step

Execute `tasks/stage-d-07-public-demo-deployment-path-and-env-wiring.md` as the next active Stage D task.

## First Task Wave

The first executable Stage D wave is complete:

- `tasks/archive/stage-d/stage-d-02-public-demo-foundation-and-guardrails.md`
- `tasks/archive/stage-d/stage-d-03-demo-content-seeding-and-showcase-path.md`
- `tasks/archive/stage-d/stage-d-04-public-demo-ops-readiness.md`

## Second Task Wave

The second executable Stage D wave is:

- `tasks/archive/stage-d/stage-d-06-public-hosting-target-and-deployment-contract.md` (complete)
- `tasks/stage-d-07-public-demo-deployment-path-and-env-wiring.md` (active)
- `tasks/stage-d-08-public-internet-rollout-and-operator-rehearsal.md` (queued)

This wave keeps Stage D focused on one bounded outcome: a real internet-accessible rollout path instead of a
well-prepared local baseline.

## Relationship To The Long-Term Roadmap

The broader future direction remains in `docs/prd/LONG_TERM_ROADMAP.md`.

That document includes:

- future Support and Job workbench layers
- staged AI capability waves such as MCP, richer agent orchestration, realtime interaction, and computer-use workflows
- longer-horizon trust and eval flywheel work

Those items are intentionally not the primary scope of Stage D.