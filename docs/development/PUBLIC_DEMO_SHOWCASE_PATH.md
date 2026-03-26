# Public Demo Showcase Path

## Purpose

This document defines the repeatable first-time-user path added in `stage-d-03`.

The public demo should no longer depend on hidden operator setup or on a collaborator guessing which documents,
questions, or task inputs will make the system look real.

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

### Hiring Review Demo

- seeded with a backend platform role brief, candidate resume, and hiring rubric
- intended value:
  - inspect the hiring packet
  - ask a grounded fit question in chat
  - run a `resume_match` task and inspect the structured review

## UI Surfaces

The guided demo path is now visible in three places:

1. home page
2. workspace hub
3. seeded workspace overview

Those surfaces should stay aligned. If a template changes, update all three through the backend-owned template catalog
instead of duplicating hard-coded content in the frontend.

## Honest Boundaries

This showcase path does not promise:

- production-grade sample-data lifecycle management
- operator-free demo refresh forever
- public data submission beyond the bounded Stage D guardrails
- deeper Support or Job workbench persistence beyond the current Stage C workflow depth

It is a repeatable public demo path, not a finished SaaS onboarding system.