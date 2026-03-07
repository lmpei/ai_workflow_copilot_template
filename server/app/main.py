from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import agents, auth, chat, documents, evals, health, metrics, tasks, workspaces
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
app.include_router(auth.router, prefix=settings.api_prefix, tags=["auth"])
app.include_router(workspaces.router, prefix=settings.api_prefix, tags=["workspaces"])
app.include_router(documents.router, prefix=settings.api_prefix, tags=["documents"])
app.include_router(chat.router, prefix=settings.api_prefix, tags=["chat"])
app.include_router(tasks.router, prefix=settings.api_prefix, tags=["tasks"])
app.include_router(agents.router, prefix=settings.api_prefix, tags=["agents"])
app.include_router(evals.router, prefix=settings.api_prefix, tags=["evals"])
app.include_router(metrics.router, prefix=settings.api_prefix, tags=["metrics"])
