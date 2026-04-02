from app.mcp.research_context_local_server import (
    RESEARCH_CONTEXT_DIGEST_RESOURCE_ID,
    RESEARCH_CONTEXT_LOCAL_MCP_SERVER_ID,
    ResearchContextLocalMcpServerError,
    build_research_context_local_mcp_server,
)
from app.schemas.mcp import (
    LocalMcpResourceReadResult,
    McpResourceDefinition,
    McpServerDefinition,
    WorkspaceConnectorMcpStatusResponse,
)
from app.services.connector_service import (
    RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
    ConnectorAccessError,
    ConnectorValidationError,
    get_workspace_connector_status,
    require_workspace_connector_consent,
)


class McpValidationError(Exception):
    pass


_RESEARCH_CONTEXT_LOCAL_MCP_SERVER = build_research_context_local_mcp_server()
_CONNECTOR_TO_SERVER_ID: dict[str, str] = {
    RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID: RESEARCH_CONTEXT_LOCAL_MCP_SERVER_ID,
}


def get_mcp_server_for_connector(connector_id: str) -> McpServerDefinition | None:
    server_id = _CONNECTOR_TO_SERVER_ID.get(connector_id)
    if server_id != RESEARCH_CONTEXT_LOCAL_MCP_SERVER_ID:
        return None
    return _RESEARCH_CONTEXT_LOCAL_MCP_SERVER.server


def get_mcp_resources_for_connector(connector_id: str) -> list[McpResourceDefinition]:
    server = get_mcp_server_for_connector(connector_id)
    if server is None:
        return []
    return list(_RESEARCH_CONTEXT_LOCAL_MCP_SERVER.resources)


def get_workspace_connector_mcp_status(
    *,
    workspace_id: str,
    user_id: str,
    connector_id: str,
) -> WorkspaceConnectorMcpStatusResponse:
    connector_status = get_workspace_connector_status(
        workspace_id=workspace_id,
        user_id=user_id,
        connector_id=connector_id,
    )
    server = get_mcp_server_for_connector(connector_id)
    if server is None:
        raise McpValidationError(f"连接器 {connector_id} 还没有绑定 MCP 服务。")
    return WorkspaceConnectorMcpStatusResponse(
        connector_status=connector_status,
        server=server,
        resources=get_mcp_resources_for_connector(connector_id),
    )


def require_workspace_mcp_resource_access(
    *,
    workspace_id: str,
    user_id: str,
    connector_id: str,
    resource_id: str,
) -> WorkspaceConnectorMcpStatusResponse:
    status = get_workspace_connector_mcp_status(
        workspace_id=workspace_id,
        user_id=user_id,
        connector_id=connector_id,
    )
    resource_ids = {resource.id for resource in status.resources}
    if resource_id not in resource_ids:
        raise McpValidationError(f"连接器 {connector_id} 不支持 MCP 资源 {resource_id}。")
    require_workspace_connector_consent(
        workspace_id=workspace_id,
        user_id=user_id,
        connector_id=connector_id,
    )
    return status


def read_workspace_mcp_resource(
    *,
    workspace_id: str,
    user_id: str,
    connector_id: str,
    resource_id: str,
    query: str,
    limit: int = 3,
) -> LocalMcpResourceReadResult:
    require_workspace_mcp_resource_access(
        workspace_id=workspace_id,
        user_id=user_id,
        connector_id=connector_id,
        resource_id=resource_id,
    )
    if connector_id != RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID:
        raise McpValidationError(f"连接器 {connector_id} 还没有对应的本地 MCP 服务。")
    if resource_id != RESEARCH_CONTEXT_DIGEST_RESOURCE_ID:
        raise McpValidationError(f"不支持的 MCP 资源：{resource_id}")
    try:
        return _RESEARCH_CONTEXT_LOCAL_MCP_SERVER.read_resource(
            resource_id=resource_id,
            query=query,
            limit=limit,
        )
    except ResearchContextLocalMcpServerError as error:
        raise McpValidationError(str(error)) from error


__all__ = [
    "ConnectorAccessError",
    "ConnectorValidationError",
    "McpValidationError",
    "RESEARCH_CONTEXT_DIGEST_RESOURCE_ID",
    "RESEARCH_CONTEXT_LOCAL_MCP_SERVER_ID",
    "RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID",
    "get_workspace_connector_mcp_status",
    "read_workspace_mcp_resource",
    "require_workspace_mcp_resource_access",
]
