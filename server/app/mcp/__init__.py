"""Bounded MCP foundations for the current product baseline."""

from app.mcp.research_context_local_server import (
    AI_FRONTIER_LOCAL_MCP_SERVER_ID,
    ResearchContextLocalMcpServer,
)
from app.schemas.mcp import AI_FRONTIER_DIGEST_RESOURCE_ID, AI_FRONTIER_STDIO_MCP_SERVER_ID

__all__ = [
    "AI_FRONTIER_DIGEST_RESOURCE_ID",
    "AI_FRONTIER_LOCAL_MCP_SERVER_ID",
    "AI_FRONTIER_STDIO_MCP_SERVER_ID",
    "ResearchContextLocalMcpServer",
]
