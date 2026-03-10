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

The repository is currently in `Phase 1: Platform MVP`.

Phase 1 is now implemented with:

- Auth boundary and browser session flow
- PostgreSQL-backed workspace persistence
- Document upload and document metadata listing
- Chat contract with persisted traces
- Workspace metrics loop
- Frontend MVP integration for auth, workspaces, documents, chat, and metrics

## Current MVP Demo Path

You can now demo the current platform MVP in this order:

1. Register or log in from `http://localhost:3000/register` or `http://localhost:3000/login`
2. Create a workspace from `http://localhost:3000/workspaces`
3. Open the workspace documents page and upload a file
4. Open the workspace chat page and submit a prompt
5. Open the workspace analytics page and inspect metrics

## Not Implemented Yet

The following capabilities remain out of scope for Phase 1:

- Real RAG retrieval and source-backed answers
- Redis-backed workers and async pipelines
- LangGraph tasks and agent orchestration
- Evaluation datasets and review workflows
- Scenario-specific job, support, and research modules

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
