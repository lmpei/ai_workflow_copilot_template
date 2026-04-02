from dataclasses import dataclass

from app.connectors.research_external_context_connector import search_research_external_context
from app.schemas.mcp import (
    LocalMcpResourceItem,
    LocalMcpResourceReadResult,
    McpResourceDefinition,
    McpServerDefinition,
)
from app.services.connector_service import RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID

RESEARCH_CONTEXT_LOCAL_MCP_SERVER_ID = "research_context_local"
RESEARCH_CONTEXT_DIGEST_RESOURCE_ID = "research.context.digest"


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
        raise ResearchContextLocalMcpServerError(f"不支持的 MCP 资源：{resource_id}")

    def read_resource(self, *, resource_id: str, query: str, limit: int = 3) -> LocalMcpResourceReadResult:
        resource = self.get_resource(resource_id)
        matches = search_research_external_context(query=query, limit=limit)
        items = tuple(
            LocalMcpResourceItem(
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
            text = "没有找到与当前问题明显相关的外部上下文摘要。"
        return LocalMcpResourceReadResult(
            server=self.server,
            resource=resource,
            text=text,
            resource_count=len(matches),
            items=items,
        )


def build_research_context_local_mcp_server() -> ResearchContextLocalMcpServer:
    server = McpServerDefinition(
        id=RESEARCH_CONTEXT_LOCAL_MCP_SERVER_ID,
        display_name="Research 本地 MCP 服务",
        summary="提供一个有边界的 Research 外部上下文资源，用来验证 MCP 资源接入、授权边界和可观测性。",
        transport="local_inproc",
        module_types=["research"],
        resource_ids=[RESEARCH_CONTEXT_DIGEST_RESOURCE_ID],
    )
    resources = (
        McpResourceDefinition(
            id=RESEARCH_CONTEXT_DIGEST_RESOURCE_ID,
            uri="mcp://research-context/digest",
            display_name="Research 外部上下文摘要",
            summary="根据当前研究问题返回一份有边界的外部上下文摘要，作为 MCP 资源试点的输入。",
            mime_type="text/markdown",
            module_types=["research"],
            connector_id=RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
        ),
    )
    return ResearchContextLocalMcpServer(server=server, resources=resources)
