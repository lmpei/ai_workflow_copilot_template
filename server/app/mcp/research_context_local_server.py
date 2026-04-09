from dataclasses import dataclass

from app.connectors.research_external_context_connector import search_research_external_context
from app.schemas.mcp import (
    AI_FRONTIER_DIGEST_RESOURCE_DISPLAY_NAME,
    AI_FRONTIER_DIGEST_RESOURCE_ID,
    AI_FRONTIER_DIGEST_RESOURCE_URI,
    AI_FRONTIER_LOCAL_MCP_SERVER_DISPLAY_NAME,
    AI_FRONTIER_LOCAL_MCP_SERVER_ID,
    McpResourceDefinition,
    McpResourceItem,
    McpResourceReadResult,
    McpServerDefinition,
)
from app.services.connector_service import RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID


class ResearchContextLocalMcpServerError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class ResearchContextLocalMcpServer:
    server: McpServerDefinition
    resources: tuple[McpResourceDefinition, ...]

    def get_resource(self, resource_id: str) -> McpResourceDefinition:
        for resource in self.resources:
            if resource.id == resource_id:
                return resource
        raise ResearchContextLocalMcpServerError(f"Unsupported MCP resource: {resource_id}")

    def read_resource(self, *, resource_id: str, query: str, limit: int = 3) -> McpResourceReadResult:
        resource = self.get_resource(resource_id)
        matches = search_research_external_context(query=query, limit=limit)
        items = tuple(
            McpResourceItem(
                resource_id=entry.context_id,
                title=entry.title,
                source_label=entry.source_label,
                snippet=entry.snippet,
            )
            for entry in matches
        )
        if matches:
            text = "\n\n".join(
                (
                    f"## {entry.title}\n"
                    f"来源：{entry.source_label}\n\n"
                    f"{entry.snippet}"
                )
                for entry in matches
            )
        else:
            text = "没有找到与当前 AI 前沿研究问题明显相关的补充上下文。"
        return McpResourceReadResult(
            server=self.server,
            resource=resource,
            text=text,
            resource_count=len(matches),
            items=items,
        )


def build_research_context_local_mcp_server() -> ResearchContextLocalMcpServer:
    server = McpServerDefinition(
        id=AI_FRONTIER_LOCAL_MCP_SERVER_ID,
        display_name=AI_FRONTIER_LOCAL_MCP_SERVER_DISPLAY_NAME,
        summary="提供一条受限的本地 MCP 摘要资源，用来对照独立 AI 前沿 MCP 服务端的主路径。",
        transport="local_inproc",
        module_types=["research"],
        resource_ids=[AI_FRONTIER_DIGEST_RESOURCE_ID],
    )
    resources = (
        McpResourceDefinition(
            id=AI_FRONTIER_DIGEST_RESOURCE_ID,
            uri=AI_FRONTIER_DIGEST_RESOURCE_URI,
            display_name=AI_FRONTIER_DIGEST_RESOURCE_DISPLAY_NAME,
            summary="根据当前问题返回一份有边界的 AI 前沿摘要。",
            mime_type="text/markdown",
            module_types=["research"],
            connector_id=RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
        ),
    )
    return ResearchContextLocalMcpServer(server=server, resources=resources)
