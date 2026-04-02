from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    agents,
    auth,
    chat,
    connectors,
    documents,
    evals,
    health,
    job_hiring_packets,
    metrics,
    public_demo,
    research_analysis_runs,
    research_assets,
    scenarios,
    support_cases,
    tasks,
    workspaces,
)
from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()
configure_logging()

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.api_prefix, tags=["health"])
app.include_router(public_demo.router, prefix=settings.api_prefix, tags=["public-demo"])
app.include_router(auth.router, prefix=settings.api_prefix, tags=["auth"])
app.include_router(scenarios.router, prefix=settings.api_prefix, tags=["scenarios"])
app.include_router(workspaces.router, prefix=settings.api_prefix, tags=["workspaces"])
app.include_router(connectors.router, prefix=settings.api_prefix, tags=["connectors"])
app.include_router(documents.router, prefix=settings.api_prefix, tags=["documents"])
app.include_router(chat.router, prefix=settings.api_prefix, tags=["chat"])
app.include_router(tasks.router, prefix=settings.api_prefix, tags=["tasks"])
app.include_router(research_analysis_runs.router, prefix=settings.api_prefix, tags=["research-analysis-runs"])
app.include_router(research_assets.router, prefix=settings.api_prefix, tags=["research-assets"])
app.include_router(support_cases.router, prefix=settings.api_prefix, tags=["support-cases"])
app.include_router(job_hiring_packets.router, prefix=settings.api_prefix, tags=["job-hiring-packets"])
app.include_router(agents.router, prefix=settings.api_prefix, tags=["agents"])
app.include_router(evals.router, prefix=settings.api_prefix, tags=["evals"])
app.include_router(metrics.router, prefix=settings.api_prefix, tags=["metrics"])
