# AI Workflow Copilot Platform

This repository is the scaffold for an AI workflow platform with:

- Next.js App Router frontend with a TypeScript-first standard
- FastAPI backend
- PostgreSQL + Redis via Docker Compose
- RAG, task, and agent scaffolding
- automated verification in CI
- project docs for product, architecture, and agent workflows

## Product direction

The target product is a platform core plus reusable scenario modules:

- Platform core: auth, workspaces, documents, chat, tasks, metrics
- Scenario modules: Job Assistant, Support Copilot, Research Assistant
- AI capabilities: retrieval, agents, async tasks, evaluation, observability

Project-level docs:

- `docs/prd/PLATFORM_PRD.md`
- `docs/architecture/PLATFORM_ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`
- `AI_WORKFLOW.md`
- `AGENT_GUIDE.md`

The frontend scaffold is now TypeScript-based. The migration record is archived in
`docs/archive/FRONTEND_TYPESCRIPT_MIGRATION.md` and `tasks/archive/frontend-typescript-migration.md`.

## AI-native workflow

This repository is designed for spec-driven human + AI collaboration.

1. Write the feature PRD in `docs/prd/`
2. Define architecture in `docs/architecture/`
3. Break work into scoped tasks in `tasks/`
4. Execute tasks with a coding agent using `prompts/CODING_AGENT_PROMPT_TEMPLATE.md`
5. Run verification before handoff
6. Review with a human before merging

See `AI_WORKFLOW.md` for the full workflow, `AGENT_GUIDE.md` for repository rules, and
`docs/review/HUMAN_REVIEW_CHECKLIST.md` for pre-merge review. Use `docs/PROJECT_GUIDE.md` as the map of
document ownership, folder responsibilities, and current project stage.

## Quick start

PowerShell on Windows:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Unix shell:

```bash
cp .env.example .env
docker compose up --build
```

Backend: `http://localhost:8000`  
Frontend: `http://localhost:3000`

For full local Windows setup and PowerShell-specific notes, see `docs/development/WINDOWS_SETUP.md`.

## Current Phase

The repository is currently in `Phase 0: Scaffold & Alignment`.

Phase 0 includes:

- Product, architecture, workflow, and review docs aligned to one roadmap
- Docker, CI, verification commands, and Windows development support
- Backend skeleton for `core/`, `models/`, `schemas/`, `repositories/`, `workers/`, and planned route groups
- Frontend route skeleton for auth, dashboard, workspace overview, documents, chat, tasks, and analytics
- Demo routes for `health`, `workspaces`, `chat`, and `metrics`

Phase 1 starts when the repository adds:

- Auth boundary and session flow
- Workspace persistence backed by PostgreSQL
- Document API surface beyond placeholders
- Stable chat, trace, and metrics contracts

## Verification

Backend:

```bash
cd server
ruff check .
mypy app
pytest
```

Windows PowerShell:

```powershell
cd server
..\.venv\Scripts\python -m ruff check .
..\.venv\Scripts\python -m mypy app
..\.venv\Scripts\python -m pytest
```

Frontend:

```bash
cd web
npm ci
npm run lint
npm run build
```

Windows PowerShell:

```powershell
cd web
npm.cmd ci
npm.cmd run verify
```

## Structure

- `AI_WORKFLOW.md` workflow contract for human + agent collaboration
- `server/` FastAPI backend
- `web/` Next.js frontend
- `docs/` PRD and architecture specs
- `scripts/` local helper scripts, including Windows setup and verification
- `tasks/` executable task specs
- `prompts/` coding agent prompt templates
- `.github/` CI and pull request templates
