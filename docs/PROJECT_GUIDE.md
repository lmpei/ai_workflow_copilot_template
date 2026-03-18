# Project Guide

## Purpose

This document explains the role of each major document and folder, and how the repository now separates live control
state from deep reference docs and task history.

## Documentation Layers

### Root Control Plane

Use these files for live coordination and orientation:

- `README.md`
  - human entry point, quick start, common commands, and doc navigation
- `AGENTS.md`
  - canonical AI rules and execution contract
- `CONTEXT.md`
  - stable project facts and boundaries
- `STATUS.md`
  - current phase, objective, blockers, and active task
- `DECISIONS.md`
  - append-only confirmed decisions
- `ARCHITECTURE.md`
  - short architecture summary

### Long-Form Docs of Record

Use these files for detailed reference material:

- `docs/prd/PLATFORM_PRD.md`
  - product scope, module responsibilities, success criteria, and phase roadmap
- `docs/prd/STAGE_A_PLAN.md`
  - formal Stage A planning document derived from the post-Phase-5 roadmap model
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
  - detailed system architecture and target boundaries
- `docs/development/DELIVERY_BASELINE.md`
  - Stage A delivery, migration, release, rollback, and runbook baseline
- `docs/development/WINDOWS_SETUP.md`
  - Windows-specific setup and local verification notes
- `docs/review/HUMAN_REVIEW_CHECKLIST.md`
  - human review checklist before merge
- `docs/archive/`
  - completed or superseded long-form docs

### Task Layer

Use these files for execution and history:

- `tasks/README.md`
  - explains active-task and archive rules
- `tasks/TASK_TEMPLATE.md`
  - task structure template
- `tasks/`
  - active execution-ready tasks
- `tasks/archive/`
  - completed tasks and execution history

Stage A work should use `stage-a-*` task naming.
Phase 5 tasks should remain archived under `tasks/archive/phase5/`.

### Workflow and Prompting

- `AI_WORKFLOW.md`
  - overall human plus AI development flow
- `prompts/CODING_AGENT_PROMPT_TEMPLATE.md`
  - reusable task-execution prompt template

## Folder Responsibilities

### Repository Root

- `server/`
  - backend application, workers, agents, and tests
- `web/`
  - frontend application, route shells, shared components, and client helpers
- `docs/`
  - long-form product, architecture, development, and review docs
- `tasks/`
  - active and archived task specs
- `prompts/`
  - coding-agent prompt templates
- `scripts/`
  - local helper scripts
- `.github/`
  - CI and pull request workflow metadata

### Backend Folders

- `server/app/core/`
  - configuration and cross-cutting runtime concerns
- `server/app/api/routes/`
  - typed REST entry points
- `server/app/models/`
  - persistence-oriented domain entities
- `server/app/schemas/`
  - request and response contracts
- `server/app/services/`
  - orchestration and business logic
- `server/app/repositories/`
  - persistence boundary
- `server/app/workers/`
  - real async job entry points only
- `server/app/agents/`
  - agent runtime, tools, and workflow logic
- `server/tests/`
  - backend verification and API-contract tests

### Frontend Folders

- `web/app/`
  - route-level UI organized by App Router structure
- `web/components/`
  - reusable UI building blocks and page sections
- `web/lib/`
  - client helpers, navigation constants, and shared logic

## Frontend Naming Defaults

- `*Manager`
  - CRUD and state-orchestration containers
- `*Panel`
  - route-facing business panels rendered directly by page shells
- `*Placeholder`
  - draft or reserved UI not yet on the live path

## Stage A Research Contract

- `research_summary` and `workspace_report` now use a Research-specific module-layer input contract instead of only a
  freeform `goal`
- canonical Research input fields are:
  - `goal`
  - `focus_areas`
  - `key_questions`
  - `constraints`
  - `deliverable`
  - `requested_sections`
  - optional follow-up fields:
    - `parent_task_id`
    - `continuation_notes`
- the shared task primitives remain generic; the structured Research contract is resolved in the Research module layer
- canonical Research results now carry both the normalized `input` and structured `sections` alongside the existing
  `summary`, `highlights`, `evidence`, and `artifacts` fields
- follow-up Research runs can also carry a structured `lineage` object that points back to the parent Research task,
  including the parent summary, optional parent goal, and optional parent report headline
- `workspace_report` and any Research run that requests `deliverable=report` can also emit a formal `report` object
  with:
  - `headline`
  - `executive_summary`
  - `sections`
  - `open_questions`
  - `recommended_next_steps`
  - `evidence_ref_ids`
- the formal report surface is evidence-led; report sections should preserve evidence reference IDs so findings stay
  grounded in workspace context
- canonical Research result metadata now also carries a Stage A trust baseline with:
  - `baseline_version`
  - `evidence_status`
  - deterministic `checks`
  - explicit `gaps`
  - `regression_passed`
- canonical Research result metadata also carries a stricter Stage A regression baseline with:
  - `baseline_version`
  - `passed`
  - `checks`
  - `issues`
  - `signals`
- the regression baseline should fail weak-context Research outputs such as `documents_only` or `no_documents`; those
  runs remain valid task results, but they are no longer treated as clean regression passes
- Research task execution now records `research_task` traces for successful and failed runs so trust signals and failure
  shapes remain inspectable after the task completes, including regression-baseline summaries on successful Research
  runs
- the Research surface now lets a user continue from a completed Research result, reusing its input shape while linking
  the new task to the parent task through Stage A follow-up lineage

## Scenario Module Boundaries

The repository hosts one shared platform core plus three scenario modules.

### Research Assistant

- Work object: workspace-scoped document sets, evidence, and open research questions
- Primary output: evidence-backed synthesis and workspace reports
- Core capabilities: grounded retrieval, multi-document summarization, viewpoint comparison, report generation
- Not responsible for: ticket triage, reply drafting, candidate-to-role matching

### Support Copilot

- Work object: support cases, tickets, and knowledge-base context
- Primary output: grounded case summaries, reply drafts, and escalation guidance
- Core capabilities: knowledge-base Q&A, ticket classification, reply drafting, escalation guidance
- Not responsible for: broad research synthesis, multi-document comparison across a large corpus, hiring evaluation

### Job Assistant

- Work object: hiring materials such as job descriptions, resumes, and fit criteria
- Primary output: structured job summaries, match assessments, and next-step recommendations
- Core capabilities: structured extraction, resume matching, gap analysis, application workflow support
- Not responsible for: support-case handling, knowledge-base reply generation, broad research report synthesis

## Live-State Rule

Do not use this guide as the live source of current project status. Use `STATUS.md` for the current objective and active
task. Use `DECISIONS.md` for confirmed choices. Use `CONTEXT.md` for stable facts.

## Alignment Rules

1. do not treat the project as a single chatbot app
2. do not bypass platform primitives for scenario-specific shortcuts
3. do not let archived tasks become the current-state source
4. update the control-plane docs when a durable project truth changes
5. prefer additive doc refactors over destructive replacement of existing history

## Stage A Delivery Baseline

- `local`, `dev`, and `staging` now have explicit intent in the docs
- `.env.example` remains a scaffold only; no shared environment should keep `replace_me`
- `scripts/migrate-windows.cmd`
  - applies Alembic migrations against the active `DATABASE_URL`
- `scripts/release-check-windows.cmd`
  - validates `.env` placeholder removal and runs the repository verification baseline
