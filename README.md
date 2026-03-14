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

Make sure Docker Desktop or the local Docker engine is running before `docker compose up --build`.

Frontend: `http://localhost:3000`  
API base: `http://localhost:8000/api/v1`  
Health check: `http://localhost:8000/api/v1/health`

For full local Windows setup and PowerShell-specific notes, see `docs/development/WINDOWS_SETUP.md`.

## Runtime Services

`docker compose up` starts the platform and its backing services together:

- `web`
  - Next.js frontend for auth, workspaces, documents, chat, and analytics
- `server`
  - FastAPI API for platform logic and orchestration
- `db`
  - PostgreSQL system of record for users, workspaces, documents, messages, traces, and embedding mappings
- `chroma`
  - Vector store used by Phase 2 ingest and retrieval-backed chat
- `redis`
  - Queue/cache service reserved for Phase 3 task execution and workers; it runs in local Docker now but is not part of the main Phase 2 request path

## Current Phase

The repository is currently in `Phase 2: Document Ingest + RAG`.

Phase 2 is now implemented with:

- Auth boundary and browser session flow
- PostgreSQL-backed workspace persistence
- Document upload, parsing, chunking, embedding, and Chroma indexing
- Reindex support through the same synchronous ingest path
- Retrieval-backed chat with grounded source citations
- Workspace metrics driven by persisted traces
- Frontend support for ingest status, reindex actions, and grounded citations
- A live provider path validated against Alibaba Cloud Model Studio's OpenAI-compatible APIs using `qwen-plus` for chat and `text-embedding-v4` for embeddings

## Current MVP Demo Path

You can now demo the current platform in this order:

1. Register or log in from `http://localhost:3000/register` or `http://localhost:3000/login`
2. Create a workspace from `http://localhost:3000/workspaces`
3. Open the workspace documents page and upload a supported text, markdown, or PDF file
4. Confirm the document reaches `indexed` status
5. Trigger `Reindex` from the documents page to refresh derived chunks and vector mappings
6. Open the workspace chat page and submit a prompt against indexed content
7. Review grounded citations and trace identifiers in chat responses
8. Open the workspace analytics page and inspect metrics

## Not Implemented Yet

The following capabilities remain out of scope for Phase 2:

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
