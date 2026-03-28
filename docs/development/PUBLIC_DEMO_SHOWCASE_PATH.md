# Public Demo Showcase Path

## Purpose

This document defines the repeatable public-demo walkthrough path that started in `stage-d-03` and was clarified again
in `stage-e-09`.

The public demo should no longer depend on hidden operator setup or on a collaborator guessing which documents,
questions, task inputs, or workbench objects should be used first.

## Backend-Owned Demo Templates

The repository now exposes one backend-owned showcase catalog:

- `GET /api/v1/public-demo/templates`
- `POST /api/v1/public-demo/templates/{template_id}/workspaces`

Those templates seed demo-safe workspaces and indexed documents for:

1. `research`
2. `support`
3. `job`

## First-Time Collaborator Flow

Use this path for anyone seeing the system for the first time:

1. open the landing page and understand the three module workflows from the guided-template cards
2. register or sign in
3. open `Workspace Hub`
4. create one `Guided Demo Workspace`
5. land in the seeded workspace overview
6. follow the guided path in this order:
   - `Documents`
   - `Chat`
   - `Tasks`

This order matters because it shows:

- the seeded source material
- grounded retrieval and citations
- the structured workflow result for the chosen module

## Existing Workspace Workbench Flow

Once Stage E added direct Support case and Job hiring-packet actions, the public demo also gained one honest path for
continuing existing work:

- Support
  - open an existing workspace
  - go to `Tasks`
  - continue from the visible Support case instead of reconstructing the next step from raw task history
- Job
  - open an existing workspace
  - go to `Tasks`
  - continue from the visible Job hiring packet instead of reconstructing the next step from raw task history
- Research
  - still follows the smaller `Documents -> Chat -> Tasks` walkthrough without a new Stage E workbench action loop

This existing-workspace path is for continuity, not for a clean first-time story. When a clean path matters, use a new
guided demo workspace.

## Showcase Templates

### Research Briefing Demo

- seeded with launch-planning, interview, and competitor-watch notes
- intended value:
  - inspect the indexed corpus
  - ask a grounded launch-risk question in chat
  - run a `research_summary` task that turns the corpus into a briefing

### Support Escalation Demo

- seeded with a password-reset knowledge base article, incident note, and escalation runbook
- intended value:
  - inspect the support knowledge base
  - ask a grounded mitigation and escalation question in chat
  - run a `ticket_summary` or `reply_draft` task and inspect the escalation packet
  - if history already exists, continue from the visible Support case workbench

### Hiring Review Demo

- seeded with a backend platform role brief, candidate resume, and hiring rubric
- intended value:
  - inspect the hiring packet
  - ask a grounded fit question in chat
  - run a `resume_match` task and inspect the structured review
  - if history already exists, continue from the visible Job hiring-packet workbench

## UI Surfaces

The guided demo path is now visible in three places:

1. home page
2. workspace hub
3. seeded workspace overview

The workbench-continuity explanation is now visible in the seeded workspace overview and in the module task surface.
Those surfaces should stay aligned. If a template changes, update all three through the backend-owned template catalog
instead of duplicating hard-coded content in the frontend.

## Honest Boundaries

This showcase path does not promise:

- production-grade sample-data lifecycle management
- operator-free demo refresh forever
- public data submission beyond the bounded Stage D guardrails
- silent cleanup of old Support case or Job hiring-packet history before a walkthrough
- workbench depth beyond the current bounded Stage E action loops

It is a repeatable public demo path, not a finished SaaS onboarding system.
