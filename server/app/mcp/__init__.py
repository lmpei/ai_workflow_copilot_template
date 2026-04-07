"""Bounded MCP foundations for Stage I."""

from app.mcp.research_context_local_server import (
    RESEARCH_CONTEXT_DIGEST_RESOURCE_ID,
    RESEARCH_CONTEXT_LOCAL_MCP_SERVER_ID,
    ResearchContextLocalMcpServer,
)
from app.schemas.mcp import RESEARCH_CONTEXT_STDIO_MCP_SERVER_ID

__all__ = [
    "RESEARCH_CONTEXT_DIGEST_RESOURCE_ID",
    "RESEARCH_CONTEXT_LOCAL_MCP_SERVER_ID",
    "RESEARCH_CONTEXT_STDIO_MCP_SERVER_ID",
    "ResearchContextLocalMcpServer",
]
