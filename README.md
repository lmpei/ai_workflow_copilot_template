# AI Workflow Copilot Platform

AI Workflow Copilot is a shared platform core for AI knowledge-work workflows. It combines workspaces, document ingest,
grounded chat, async tasks, agent execution, evaluation, and observability so reusable scenario modules can run on the
same system.

## Overview

The platform currently supports three scenario modules on one shared core:

- Research Assistant
- Support Copilot
- Job Assistant

The codebase is designed for spec-driven human plus AI collaboration. The repository keeps long-form product and
architecture docs under `docs/`, task execution history under `tasks/archive/`, and live control-plane docs at the
repository root.

## Quick Start

1. Copy the example environment file.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Unix shell:

```bash
cp .env.example .env
```

2. Edit `.env` and replace `AUTH_SECRET_KEY=replace_me` with your own unique secret.

3. Start the stack.

```bash
docker compose up --build
```

Frontend: `http://localhost:3000`
API base: `http://localhost:8000/api/v1`
Health check: `http://localhost:8000/api/v1/health`

For Windows-specific setup notes, see `docs/development/WINDOWS_SETUP.md`.
For the concrete staging rehearsal path, see `docs/development/STAGING_RELEASE_PATH.md`.
For the Stage C cross-module demo baseline, see `docs/development/STAGE_C_CROSS_MODULE_READINESS.md`.
For the reusable Stage C rehearsal evidence shape, see `docs/development/STAGE_C_REHEARSAL_EVIDENCE_TEMPLATE.md`.

## Common Commands

Backend:

```powershell
cd server
..\.venv\Scripts\python.exe -m pytest tests
```

Frontend:

```powershell
npm --prefix web run verify
```

## Project Control Docs

Start here when you need to understand the project quickly:

- `AGENTS.md`
  - AI collaboration rules and execution contract
- `STATUS.md`
  - current state, current objective, blockers, and active task
- `CONTEXT.md`
  - stable project facts, stack, and boundaries
- `DECISIONS.md`
  - confirmed decisions and sequencing choices
- `ARCHITECTURE.md`
  - short architecture summary

## Detailed Docs of Record

Use these when you need deeper reference material:

- `docs/prd/PLATFORM_PRD.md`
- `docs/prd/STAGE_A_PLAN.md`
- `docs/prd/STAGE_B_PLAN.md`
- `docs/prd/STAGE_C_PLAN.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/development/DELIVERY_BASELINE.md`
- `docs/development/STAGING_RELEASE_PATH.md`
- `docs/development/STAGING_RELEASE_EVIDENCE_TEMPLATE.md`
- `docs/development/STAGING_HANDOFF_TEMPLATE.md`
- `docs/development/STAGE_C_CROSS_MODULE_READINESS.md`
- `docs/development/STAGE_C_REHEARSAL_EVIDENCE_TEMPLATE.md`
- `docs/PROJECT_GUIDE.md`
- `AI_WORKFLOW.md`
- `tasks/README.md`

## Current State

The latest live state is maintained in `STATUS.md`.

At a high level, the repository has a Phase 5 baseline implemented, has completed `Stage A`, has completed and closed
`Stage B`, has completed the first and second `Stage C` waves, and is now awaiting the next Stage C planning decision
under the three-track roadmap model in `docs/prd/STAGE_C_PLAN.md`.

## Runtime Services

`docker compose up` starts:

- `web`
  - Next.js frontend for auth, workspaces, documents, chat, tasks, evaluations, and analytics
- `server`
  - FastAPI API for platform logic, orchestration, evaluation runs, and observability surfaces
- `db`
  - PostgreSQL system of record
- `chroma`
  - vector store for retrieval-backed features
- `redis`
  - queue backend for ARQ workers

## Repository Structure

- `server/`
  - backend application, workers, agents, and tests
- `web/`
  - frontend application, shared components, and client helpers
- `docs/`
  - long-form product, architecture, development, and review docs
- `tasks/`
  - active and archived task specs
- `prompts/`
  - coding-agent prompt templates
- `scripts/`
  - local helper scripts

## Verification

Backend baseline:

```powershell
cd server
..\.venv\Scripts\python.exe -m pytest tests
```

Frontend baseline:

```powershell
npm --prefix web run verify
```

Migration baseline:

```powershell
cmd /c scripts\migrate-windows.cmd .env
```

Stage B release preflight baseline:

```powershell
cmd /c scripts\release-check-windows.cmd .env
```

Stage B staging smoke baseline:

```powershell
cmd /c scripts\staging-smoke-windows.cmd .env.staging
```

Stage B rehearsal helper:

```powershell
cmd /c scripts\staging-rehearse-windows.cmd .env.staging <rollback-target> app-tier C:\staging\handoff.md C:\staging\evidence.md
```
