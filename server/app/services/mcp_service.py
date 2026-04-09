from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.mcp.research_context_local_server import (
    AI_FRONTIER_LOCAL_MCP_SERVER_ID,
    ResearchContextLocalMcpServerError,
    build_research_context_local_mcp_server,
)
from app.mcp.stdio_process_client import (
    McpProcessClientError,
    call_stdio_mcp_tool,
    describe_stdio_mcp_server,
    get_stdio_mcp_prompt,
    read_stdio_mcp_resource,
)
from app.schemas.mcp import (
    AI_FRONTIER_BRIEF_PROMPT_DISPLAY_NAME,
    AI_FRONTIER_BRIEF_PROMPT_NAME,
    AI_FRONTIER_DIGEST_RESOURCE_DISPLAY_NAME,
    AI_FRONTIER_DIGEST_RESOURCE_ID,
    AI_FRONTIER_DIGEST_RESOURCE_URI,
    AI_FRONTIER_EXTERNAL_MCP_SERVER_DISPLAY_NAME,
    AI_FRONTIER_EXTERNAL_MCP_SERVER_ID,
    AI_FRONTIER_SEARCH_TOOL_DISPLAY_NAME,
    AI_FRONTIER_SEARCH_TOOL_NAME,
    AI_FRONTIER_STDIO_MCP_SERVER_DISPLAY_NAME,
    AI_FRONTIER_STDIO_MCP_SERVER_ID,
    McpEndpointAuthState,
    McpEndpointDefinition,
    McpPromptDefinition,
    McpPromptRenderResult,
    McpResourceDefinition,
    McpResourceReadResult,
    McpServerDefinition,
    McpStdioServerConfig,
    McpToolCallResult,
    McpToolDefinition,
    WorkspaceConnectorMcpStatusResponse,
    WorkspaceConnectorMcpValidationResponse,
)
from app.services.connector_service import (
    RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
    get_workspace_connector_status,
    require_workspace_connector_consent,
)


class McpValidationError(Exception):
    pass


class McpRemoteTransportError(McpValidationError):
    pass


class McpExternalEndpointNotConfiguredError(McpValidationError):
    pass


class McpRemoteAuthRequiredError(McpValidationError):
    pass


class McpRemoteAuthDeniedError(McpValidationError):
    pass


_SERVER_ROOT = Path(__file__).resolve().parents[2]
_AI_FRONTIER_LOCAL_MCP_SERVER = build_research_context_local_mcp_server()
_AI_FRONTIER_STDIO_MCP_SERVER = McpServerDefinition(
    id=AI_FRONTIER_STDIO_MCP_SERVER_ID,
    display_name=AI_FRONTIER_STDIO_MCP_SERVER_DISPLAY_NAME,
    summary="通过仓库内的进程外 MCP 服务维持一条受限基线，便于对照独立 weave-mcp-server 的真实接入。",
    transport="stdio_process",
    module_types=["research"],
    resource_ids=[AI_FRONTIER_DIGEST_RESOURCE_ID],
)
_AI_FRONTIER_STDIO_MCP_CONFIG = McpStdioServerConfig(
    module="app.mcp.research_context_stdio_server",
    working_directory=str(_SERVER_ROOT),
)
_CONNECTOR_TO_SERVER_ID: dict[str, str] = {
    RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID: AI_FRONTIER_STDIO_MCP_SERVER_ID,
}


def _get_local_resources() -> list[McpResourceDefinition]:
    return list(_AI_FRONTIER_LOCAL_MCP_SERVER.resources)


def _get_local_tools() -> list[McpToolDefinition]:
    return []


def _get_local_prompts() -> list[McpPromptDefinition]:
    return []


def _build_repo_local_endpoint_definition() -> McpEndpointDefinition:
    return McpEndpointDefinition(
        source="repo_local",
        display_name=AI_FRONTIER_STDIO_MCP_SERVER_DISPLAY_NAME,
        transport="stdio_process",
        launch_kind="python_module",
        working_directory=str(_SERVER_ROOT),
        target_hint="python -m app.mcp.research_context_stdio_server",
    )


def _build_external_mcp_endpoint_definition() -> McpEndpointDefinition | None:
    settings = get_settings()
    if not settings.research_external_mcp_enabled:
        return None
    if not settings.research_external_mcp_command:
        return None
    if not settings.research_external_mcp_working_directory.strip():
        return None
    return McpEndpointDefinition(
        source="external_configured",
        display_name=settings.research_external_mcp_server_display_name,
        transport="stdio_process",
        launch_kind="command",
        working_directory=settings.research_external_mcp_working_directory,
        target_hint=" ".join(settings.research_external_mcp_command),
    )


def _build_external_mcp_server_definition() -> McpServerDefinition | None:
    endpoint = _build_external_mcp_endpoint_definition()
    if endpoint is None:
        return None
    settings = get_settings()
    return McpServerDefinition(
        id=settings.research_external_mcp_server_id or AI_FRONTIER_EXTERNAL_MCP_SERVER_ID,
        display_name=settings.research_external_mcp_server_display_name or AI_FRONTIER_EXTERNAL_MCP_SERVER_DISPLAY_NAME,
        summary=settings.research_external_mcp_server_summary,
        transport="stdio_process",
        module_types=["research"],
        resource_ids=[settings.research_external_mcp_resource_id],
        tool_names=[AI_FRONTIER_SEARCH_TOOL_NAME],
        prompt_names=[AI_FRONTIER_BRIEF_PROMPT_NAME],
    )


def _build_external_mcp_resource_definition(connector_id: str) -> McpResourceDefinition | None:
    endpoint = _build_external_mcp_endpoint_definition()
    if endpoint is None:
        return None
    settings = get_settings()
    return McpResourceDefinition(
        id=settings.research_external_mcp_resource_id or AI_FRONTIER_DIGEST_RESOURCE_ID,
        uri=settings.research_external_mcp_resource_uri or AI_FRONTIER_DIGEST_RESOURCE_URI,
        display_name=settings.research_external_mcp_resource_display_name or AI_FRONTIER_DIGEST_RESOURCE_DISPLAY_NAME,
        summary=settings.research_external_mcp_resource_summary,
        mime_type="text/plain",
        module_types=["research"],
        connector_id=connector_id,
    )


def _build_external_mcp_tool_definition(connector_id: str) -> McpToolDefinition | None:
    endpoint = _build_external_mcp_endpoint_definition()
    if endpoint is None:
        return None
    return McpToolDefinition(
        name=AI_FRONTIER_SEARCH_TOOL_NAME,
        display_name=AI_FRONTIER_SEARCH_TOOL_DISPLAY_NAME,
        summary="搜索独立 MCP 服务端里的 AI 前沿项目、事件与框架信息。",
        module_types=["research"],
        connector_id=connector_id,
    )


def _build_external_mcp_prompt_definition(connector_id: str) -> McpPromptDefinition | None:
    endpoint = _build_external_mcp_endpoint_definition()
    if endpoint is None:
        return None
    return McpPromptDefinition(
        name=AI_FRONTIER_BRIEF_PROMPT_NAME,
        display_name=AI_FRONTIER_BRIEF_PROMPT_DISPLAY_NAME,
        summary="生成一份可复用的 AI 前沿研究 brief。",
        module_types=["research"],
        connector_id=connector_id,
    )


def _build_external_mcp_config() -> McpStdioServerConfig | None:
    endpoint = _build_external_mcp_endpoint_definition()
    if endpoint is None:
        return None
    settings = get_settings()
    env_overrides: dict[str, str] = {}
    if settings.research_external_mcp_expected_auth_token:
        env_overrides["WEAVE_MCP_EXPECTED_BEARER_TOKEN"] = settings.research_external_mcp_expected_auth_token
    return McpStdioServerConfig(
        launch_kind="command",
        command=list(settings.research_external_mcp_command),
        working_directory=settings.research_external_mcp_working_directory,
        auth_token=settings.research_external_mcp_auth_token or None,
        env_overrides=env_overrides,
    )


def _get_repo_local_auth_state() -> tuple[McpEndpointAuthState, str | None]:
    return "not_required", None


def _get_external_auth_state() -> tuple[McpEndpointAuthState, str | None]:
    settings = get_settings()
    if not settings.research_external_mcp_auth_required:
        return "not_required", None
    if settings.research_external_mcp_auth_token.strip():
        return "configured", "外部 MCP 访问令牌已配置。"
    return "missing", "外部 MCP 访问令牌是必需的，但当前还没有配置。"


def _normalize_server_for_endpoint(
    *,
    endpoint: McpEndpointDefinition,
    fallback_server: McpServerDefinition,
) -> McpServerDefinition:
    if endpoint.source != "external_configured":
        return fallback_server
    configured_server = _build_external_mcp_server_definition()
    return configured_server or fallback_server


def _get_repo_local_endpoint_binding(
    connector_id: str,
) -> tuple[
    McpEndpointDefinition,
    McpServerDefinition,
    list[McpResourceDefinition],
    list[McpToolDefinition],
    list[McpPromptDefinition],
    McpStdioServerConfig,
]:
    return (
        _build_repo_local_endpoint_definition(),
        _AI_FRONTIER_STDIO_MCP_SERVER,
        _get_local_resources(),
        _get_local_tools(),
        _get_local_prompts(),
        _AI_FRONTIER_STDIO_MCP_CONFIG,
    )


def _get_external_endpoint_binding(
    connector_id: str,
) -> tuple[
    McpEndpointDefinition,
    McpServerDefinition,
    list[McpResourceDefinition],
    list[McpToolDefinition],
    list[McpPromptDefinition],
    McpStdioServerConfig,
]:
    endpoint = _build_external_mcp_endpoint_definition()
    server = _build_external_mcp_server_definition()
    resource = _build_external_mcp_resource_definition(connector_id)
    tool = _build_external_mcp_tool_definition(connector_id)
    prompt = _build_external_mcp_prompt_definition(connector_id)
    config = _build_external_mcp_config()
    if endpoint is None or server is None or resource is None or tool is None or prompt is None or config is None:
        raise McpExternalEndpointNotConfiguredError("True external MCP endpoint is not configured for this connector")
    return endpoint, server, [resource], [tool], [prompt], config


def _get_configured_endpoint_binding(
    connector_id: str,
) -> tuple[
    McpEndpointDefinition,
    McpServerDefinition,
    list[McpResourceDefinition],
    list[McpToolDefinition],
    list[McpPromptDefinition],
    McpStdioServerConfig,
]:
    try:
        return _get_external_endpoint_binding(connector_id)
    except McpExternalEndpointNotConfiguredError:
        return _get_repo_local_endpoint_binding(connector_id)


def _describe_remote_server_from_binding(
    *,
    endpoint: McpEndpointDefinition,
    config: McpStdioServerConfig,
) -> tuple[McpServerDefinition, list[McpResourceDefinition], list[McpToolDefinition], list[McpPromptDefinition]]:
    try:
        server, resources, tools, prompts = describe_stdio_mcp_server(config=config)
    except McpProcessClientError as error:
        if error.code == -32010:
            raise McpRemoteAuthRequiredError(str(error)) from error
        if error.code == -32011:
            raise McpRemoteAuthDeniedError(str(error)) from error
        raise McpRemoteTransportError(str(error)) from error
    return _normalize_server_for_endpoint(endpoint=endpoint, fallback_server=server), resources, tools, prompts


def _read_remote_resource_from_binding(
    *,
    endpoint: McpEndpointDefinition,
    config: McpStdioServerConfig,
    resource_id: str,
    resource_uri: str,
    query: str,
    limit: int,
) -> McpResourceReadResult:
    try:
        result = read_stdio_mcp_resource(
            config=config,
            resource_id=resource_id,
            resource_uri=resource_uri,
            query=query,
            limit=limit,
        )
    except McpProcessClientError as error:
        if error.code == -32010:
            raise McpRemoteAuthRequiredError(str(error)) from error
        if error.code == -32011:
            raise McpRemoteAuthDeniedError(str(error)) from error
        raise McpRemoteTransportError(str(error)) from error
    return McpResourceReadResult(
        server=_normalize_server_for_endpoint(endpoint=endpoint, fallback_server=result.server),
        resource=result.resource,
        text=result.text,
        resource_count=result.resource_count,
        items=result.items,
    )


def _call_remote_tool_from_binding(
    *,
    endpoint: McpEndpointDefinition,
    config: McpStdioServerConfig,
    tool_name: str,
    arguments: dict[str, Any],
) -> McpToolCallResult:
    try:
        result = call_stdio_mcp_tool(
            config=config,
            tool_name=tool_name,
            arguments=arguments,
        )
    except McpProcessClientError as error:
        if error.code == -32010:
            raise McpRemoteAuthRequiredError(str(error)) from error
        if error.code == -32011:
            raise McpRemoteAuthDeniedError(str(error)) from error
        raise McpRemoteTransportError(str(error)) from error
    return McpToolCallResult(
        server=_normalize_server_for_endpoint(endpoint=endpoint, fallback_server=result.server),
        tool=result.tool,
        structured_content=result.structured_content,
        text_content=result.text_content,
        is_error=result.is_error,
    )


def _get_remote_prompt_from_binding(
    *,
    endpoint: McpEndpointDefinition,
    config: McpStdioServerConfig,
    prompt_name: str,
    arguments: dict[str, str],
) -> McpPromptRenderResult:
    try:
        result = get_stdio_mcp_prompt(
            config=config,
            prompt_name=prompt_name,
            arguments=arguments,
        )
    except McpProcessClientError as error:
        if error.code == -32010:
            raise McpRemoteAuthRequiredError(str(error)) from error
        if error.code == -32011:
            raise McpRemoteAuthDeniedError(str(error)) from error
        raise McpRemoteTransportError(str(error)) from error
    return McpPromptRenderResult(
        server=_normalize_server_for_endpoint(endpoint=endpoint, fallback_server=result.server),
        prompt=result.prompt,
        description=result.description,
        text=result.text,
    )


def get_mcp_server_for_connector(connector_id: str) -> McpServerDefinition | None:
    if connector_id not in _CONNECTOR_TO_SERVER_ID:
        return None
    return _get_configured_endpoint_binding(connector_id)[1]


def get_mcp_resources_for_connector(connector_id: str) -> list[McpResourceDefinition]:
    if connector_id not in _CONNECTOR_TO_SERVER_ID:
        return []
    return _get_configured_endpoint_binding(connector_id)[2]


def get_mcp_tools_for_connector(connector_id: str) -> list[McpToolDefinition]:
    if connector_id not in _CONNECTOR_TO_SERVER_ID:
        return []
    return _get_configured_endpoint_binding(connector_id)[3]


def get_mcp_prompts_for_connector(connector_id: str) -> list[McpPromptDefinition]:
    if connector_id not in _CONNECTOR_TO_SERVER_ID:
        return []
    return _get_configured_endpoint_binding(connector_id)[4]


def describe_workspace_true_external_mcp_endpoint(
    *,
    workspace_id: str,
    user_id: str,
    connector_id: str,
) -> tuple[McpEndpointDefinition | None, McpEndpointAuthState, str | None]:
    get_workspace_connector_status(
        workspace_id=workspace_id,
        user_id=user_id,
        connector_id=connector_id,
    )
    if connector_id not in _CONNECTOR_TO_SERVER_ID:
        raise McpValidationError(f"Unsupported MCP connector: {connector_id}")
    return _build_external_mcp_endpoint_definition(), *_get_external_auth_state()


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
    if connector_id not in _CONNECTOR_TO_SERVER_ID:
        raise McpValidationError(f"连接器 {connector_id} 还没有绑定 MCP 服务。")
    endpoint, server, resources, tools, prompts, _ = _get_configured_endpoint_binding(connector_id)
    auth_state, auth_detail = (
        _get_external_auth_state() if endpoint.source == "external_configured" else _get_repo_local_auth_state()
    )
    return WorkspaceConnectorMcpStatusResponse(
        connector_status=connector_status,
        endpoint=endpoint,
        auth_state=auth_state,
        auth_detail=auth_detail,
        server=server,
        resources=resources,
        tools=tools,
        prompts=prompts,
    )


def validate_workspace_connector_mcp_endpoint(
    *,
    workspace_id: str,
    user_id: str,
    connector_id: str,
) -> WorkspaceConnectorMcpValidationResponse:
    connector_status = get_workspace_connector_status(
        workspace_id=workspace_id,
        user_id=user_id,
        connector_id=connector_id,
    )
    if connector_id not in _CONNECTOR_TO_SERVER_ID:
        raise McpValidationError(f"连接器 {connector_id} 还没有绑定 MCP 服务。")
    try:
        endpoint, _, _, _, _, config = _get_external_endpoint_binding(connector_id)
    except McpExternalEndpointNotConfiguredError as error:
        repo_local_endpoint, _, resources, tools, prompts, _ = _get_repo_local_endpoint_binding(connector_id)
        auth_state, auth_detail = _get_external_auth_state()
        return WorkspaceConnectorMcpValidationResponse(
            connector_status=connector_status,
            endpoint=repo_local_endpoint,
            auth_state=auth_state,
            auth_detail=auth_detail,
            health_status="not_configured",
            health_detail=str(error),
            resources=resources,
            tools=tools,
            prompts=prompts,
        )

    auth_state, auth_detail = _get_external_auth_state()
    if auth_state == "missing":
        return WorkspaceConnectorMcpValidationResponse(
            connector_status=connector_status,
            endpoint=endpoint,
            auth_state=auth_state,
            auth_detail=auth_detail,
            health_status="invalid",
            health_detail=auth_detail,
        )

    try:
        server, resources, tools, prompts = _describe_remote_server_from_binding(endpoint=endpoint, config=config)
    except McpRemoteAuthRequiredError as error:
        return WorkspaceConnectorMcpValidationResponse(
            connector_status=connector_status,
            endpoint=endpoint,
            auth_state="missing",
            auth_detail=str(error),
            health_status="invalid",
            health_detail=str(error),
        )
    except McpRemoteAuthDeniedError as error:
        return WorkspaceConnectorMcpValidationResponse(
            connector_status=connector_status,
            endpoint=endpoint,
            auth_state="denied",
            auth_detail=str(error),
            health_status="invalid",
            health_detail=str(error),
        )
    except McpRemoteTransportError as error:
        return WorkspaceConnectorMcpValidationResponse(
            connector_status=connector_status,
            endpoint=endpoint,
            auth_state=auth_state,
            auth_detail=auth_detail,
            health_status="unreachable",
            health_detail=str(error),
        )
    return WorkspaceConnectorMcpValidationResponse(
        connector_status=connector_status,
        endpoint=endpoint,
        auth_state=auth_state,
        auth_detail=auth_detail,
        health_status="ready",
        server=server,
        resources=resources,
        tools=tools,
        prompts=prompts,
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


def require_workspace_mcp_tool_access(
    *,
    workspace_id: str,
    user_id: str,
    connector_id: str,
    tool_name: str,
) -> WorkspaceConnectorMcpStatusResponse:
    status = get_workspace_connector_mcp_status(
        workspace_id=workspace_id,
        user_id=user_id,
        connector_id=connector_id,
    )
    tool_names = {tool.name for tool in status.tools}
    if tool_name not in tool_names:
        raise McpValidationError(f"连接器 {connector_id} 不支持 MCP 工具 {tool_name}。")
    require_workspace_connector_consent(
        workspace_id=workspace_id,
        user_id=user_id,
        connector_id=connector_id,
    )
    return status


def require_workspace_mcp_prompt_access(
    *,
    workspace_id: str,
    user_id: str,
    connector_id: str,
    prompt_name: str,
) -> WorkspaceConnectorMcpStatusResponse:
    status = get_workspace_connector_mcp_status(
        workspace_id=workspace_id,
        user_id=user_id,
        connector_id=connector_id,
    )
    prompt_names = {prompt.name for prompt in status.prompts}
    if prompt_name not in prompt_names:
        raise McpValidationError(f"连接器 {connector_id} 不支持 MCP 提示 {prompt_name}。")
    require_workspace_connector_consent(
        workspace_id=workspace_id,
        user_id=user_id,
        connector_id=connector_id,
    )
    return status


def describe_workspace_true_external_mcp_server(
    *,
    workspace_id: str,
    user_id: str,
    connector_id: str,
) -> tuple[McpServerDefinition, list[McpResourceDefinition], list[McpToolDefinition], list[McpPromptDefinition]]:
    get_workspace_connector_status(
        workspace_id=workspace_id,
        user_id=user_id,
        connector_id=connector_id,
    )
    if connector_id not in _CONNECTOR_TO_SERVER_ID:
        raise McpValidationError(f"连接器 {connector_id} 还没有绑定进程外 MCP 服务。")
    endpoint, _, _, _, _, config = _get_external_endpoint_binding(connector_id)
    return _describe_remote_server_from_binding(endpoint=endpoint, config=config)


def describe_workspace_remote_mcp_server(
    *,
    workspace_id: str,
    user_id: str,
    connector_id: str,
) -> tuple[McpServerDefinition, list[McpResourceDefinition], list[McpToolDefinition], list[McpPromptDefinition]]:
    get_workspace_connector_status(
        workspace_id=workspace_id,
        user_id=user_id,
        connector_id=connector_id,
    )
    if connector_id not in _CONNECTOR_TO_SERVER_ID:
        raise McpValidationError(f"连接器 {connector_id} 还没有绑定进程外 MCP 服务。")
    endpoint, _, _, _, _, config = _get_configured_endpoint_binding(connector_id)
    return _describe_remote_server_from_binding(endpoint=endpoint, config=config)


def read_workspace_mcp_resource(
    *,
    workspace_id: str,
    user_id: str,
    connector_id: str,
    resource_id: str,
    query: str,
    limit: int = 3,
) -> McpResourceReadResult:
    require_workspace_mcp_resource_access(
        workspace_id=workspace_id,
        user_id=user_id,
        connector_id=connector_id,
        resource_id=resource_id,
    )
    if connector_id != RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID:
        raise McpValidationError(f"连接器 {connector_id} 还没有对应的本地 MCP 服务。")
    if resource_id != AI_FRONTIER_DIGEST_RESOURCE_ID:
        raise McpValidationError(f"不支持的 MCP 资源：{resource_id}")
    try:
        return _AI_FRONTIER_LOCAL_MCP_SERVER.read_resource(
            resource_id=resource_id,
            query=query,
            limit=limit,
        )
    except ResearchContextLocalMcpServerError as error:
        raise McpValidationError(str(error)) from error


def read_workspace_remote_mcp_resource(
    *,
    workspace_id: str,
    user_id: str,
    connector_id: str,
    resource_id: str,
    query: str,
    limit: int = 3,
) -> McpResourceReadResult:
    status = require_workspace_mcp_resource_access(
        workspace_id=workspace_id,
        user_id=user_id,
        connector_id=connector_id,
        resource_id=resource_id,
    )
    if connector_id not in _CONNECTOR_TO_SERVER_ID:
        raise McpValidationError(f"连接器 {connector_id} 还没有绑定进程外 MCP 服务。")
    endpoint, _, _, _, _, config = _get_configured_endpoint_binding(connector_id)
    resource = next(resource for resource in status.resources if resource.id == resource_id)
    return _read_remote_resource_from_binding(
        endpoint=endpoint,
        config=config,
        resource_id=resource.id,
        resource_uri=resource.uri,
        query=query,
        limit=limit,
    )


def read_workspace_true_external_mcp_resource(
    *,
    workspace_id: str,
    user_id: str,
    connector_id: str,
    resource_id: str,
    query: str,
    limit: int = 3,
) -> McpResourceReadResult:
    status = require_workspace_mcp_resource_access(
        workspace_id=workspace_id,
        user_id=user_id,
        connector_id=connector_id,
        resource_id=resource_id,
    )
    if connector_id not in _CONNECTOR_TO_SERVER_ID:
        raise McpValidationError(f"连接器 {connector_id} 还没有绑定进程外 MCP 服务。")
    endpoint, _, _, _, _, config = _get_external_endpoint_binding(connector_id)
    resource = next(resource for resource in status.resources if resource.id == resource_id)
    return _read_remote_resource_from_binding(
        endpoint=endpoint,
        config=config,
        resource_id=resource.id,
        resource_uri=resource.uri,
        query=query,
        limit=limit,
    )


def call_workspace_true_external_mcp_tool(
    *,
    workspace_id: str,
    user_id: str,
    connector_id: str,
    tool_name: str,
    arguments: dict[str, Any],
) -> McpToolCallResult:
    require_workspace_mcp_tool_access(
        workspace_id=workspace_id,
        user_id=user_id,
        connector_id=connector_id,
        tool_name=tool_name,
    )
    if connector_id not in _CONNECTOR_TO_SERVER_ID:
        raise McpValidationError(f"连接器 {connector_id} 还没有绑定进程外 MCP 服务。")
    endpoint, _, _, _, _, config = _get_external_endpoint_binding(connector_id)
    return _call_remote_tool_from_binding(
        endpoint=endpoint,
        config=config,
        tool_name=tool_name,
        arguments=arguments,
    )


def get_workspace_true_external_mcp_prompt(
    *,
    workspace_id: str,
    user_id: str,
    connector_id: str,
    prompt_name: str,
    arguments: dict[str, str],
) -> McpPromptRenderResult:
    require_workspace_mcp_prompt_access(
        workspace_id=workspace_id,
        user_id=user_id,
        connector_id=connector_id,
        prompt_name=prompt_name,
    )
    if connector_id not in _CONNECTOR_TO_SERVER_ID:
        raise McpValidationError(f"连接器 {connector_id} 还没有绑定进程外 MCP 服务。")
    endpoint, _, _, _, _, config = _get_external_endpoint_binding(connector_id)
    return _get_remote_prompt_from_binding(
        endpoint=endpoint,
        config=config,
        prompt_name=prompt_name,
        arguments=arguments,
    )


__all__ = [
    "AI_FRONTIER_DIGEST_RESOURCE_ID",
    "AI_FRONTIER_EXTERNAL_MCP_SERVER_ID",
    "AI_FRONTIER_LOCAL_MCP_SERVER_ID",
    "AI_FRONTIER_SEARCH_TOOL_NAME",
    "AI_FRONTIER_STDIO_MCP_SERVER_ID",
    "AI_FRONTIER_BRIEF_PROMPT_NAME",
    "McpExternalEndpointNotConfiguredError",
    "McpRemoteAuthDeniedError",
    "McpRemoteAuthRequiredError",
    "McpRemoteTransportError",
    "McpValidationError",
    "call_workspace_true_external_mcp_tool",
    "describe_workspace_remote_mcp_server",
    "describe_workspace_true_external_mcp_endpoint",
    "describe_workspace_true_external_mcp_server",
    "get_mcp_prompts_for_connector",
    "get_mcp_resources_for_connector",
    "get_mcp_server_for_connector",
    "get_mcp_tools_for_connector",
    "get_workspace_connector_mcp_status",
    "get_workspace_true_external_mcp_prompt",
    "read_workspace_mcp_resource",
    "read_workspace_remote_mcp_resource",
    "read_workspace_true_external_mcp_resource",
    "require_workspace_mcp_prompt_access",
    "require_workspace_mcp_resource_access",
    "require_workspace_mcp_tool_access",
    "validate_workspace_connector_mcp_endpoint",
]
