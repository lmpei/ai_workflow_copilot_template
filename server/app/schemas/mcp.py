from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.connector import WorkspaceConnectorStatusResponse

McpTransportKind = Literal["local_inproc", "stdio_process"]
McpEndpointSource = Literal["repo_local", "external_configured"]
McpEndpointHealthStatus = Literal["ready", "not_configured", "unreachable", "invalid"]
McpEndpointAuthState = Literal["not_required", "configured", "missing", "denied"]
RemoteMcpReadStatus = Literal[
    "consent_required",
    "consent_revoked",
    "auth_required",
    "auth_denied",
    "snapshot_reused",
    "used",
    "transport_unavailable",
    "no_useful_matches",
]


class McpServerDefinition(BaseModel):
    id: str
    display_name: str
    summary: str
    transport: McpTransportKind
    module_types: list[str]
    resource_ids: list[str]
    tool_names: list[str] = Field(default_factory=list)
    prompt_names: list[str] = Field(default_factory=list)
    pilot_status: Literal["bounded_pilot"] = "bounded_pilot"


class McpResourceDefinition(BaseModel):
    id: str
    uri: str
    display_name: str
    summary: str
    mime_type: Literal["text/markdown", "text/plain"]
    module_types: list[str]
    connector_id: str
    resource_kind: Literal["resource"] = "resource"
    pilot_status: Literal["bounded_pilot"] = "bounded_pilot"


class McpToolDefinition(BaseModel):
    name: str
    display_name: str
    summary: str
    module_types: list[str]
    connector_id: str
    tool_kind: Literal["tool"] = "tool"
    pilot_status: Literal["bounded_pilot"] = "bounded_pilot"


class McpPromptDefinition(BaseModel):
    name: str
    display_name: str
    summary: str
    module_types: list[str]
    connector_id: str
    prompt_kind: Literal["prompt"] = "prompt"
    pilot_status: Literal["bounded_pilot"] = "bounded_pilot"


class McpEndpointDefinition(BaseModel):
    source: McpEndpointSource
    display_name: str
    transport: McpTransportKind
    launch_kind: Literal["python_module", "command"]
    working_directory: str
    target_hint: str


class WorkspaceConnectorMcpStatusResponse(BaseModel):
    connector_status: WorkspaceConnectorStatusResponse
    endpoint: McpEndpointDefinition
    auth_state: McpEndpointAuthState
    auth_detail: str | None = None
    server: McpServerDefinition
    resources: list[McpResourceDefinition]
    tools: list[McpToolDefinition] = Field(default_factory=list)
    prompts: list[McpPromptDefinition] = Field(default_factory=list)


class WorkspaceConnectorMcpValidationResponse(BaseModel):
    connector_status: WorkspaceConnectorStatusResponse
    endpoint: McpEndpointDefinition
    auth_state: McpEndpointAuthState
    auth_detail: str | None = None
    health_status: McpEndpointHealthStatus
    health_detail: str | None = None
    server: McpServerDefinition | None = None
    resources: list[McpResourceDefinition] = Field(default_factory=list)
    tools: list[McpToolDefinition] = Field(default_factory=list)
    prompts: list[McpPromptDefinition] = Field(default_factory=list)


class McpStdioServerConfig(BaseModel):
    transport: Literal["stdio_process"] = "stdio_process"
    launch_kind: Literal["python_module", "command"] = "python_module"
    module: str | None = None
    command: list[str] = Field(default_factory=list)
    args: list[str] = Field(default_factory=list)
    working_directory: str
    auth_token: str | None = None
    env_overrides: dict[str, str] = Field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class McpResourceItem:
    resource_id: str
    title: str
    source_label: str
    snippet: str


@dataclass(frozen=True, slots=True)
class McpResourceReadResult:
    server: McpServerDefinition
    resource: McpResourceDefinition
    text: str
    resource_count: int
    items: tuple[McpResourceItem, ...] = ()


@dataclass(frozen=True, slots=True)
class McpToolCallResult:
    server: McpServerDefinition
    tool: McpToolDefinition
    structured_content: dict[str, Any] | None
    text_content: str | None
    is_error: bool = False


@dataclass(frozen=True, slots=True)
class McpPromptRenderResult:
    server: McpServerDefinition
    prompt: McpPromptDefinition
    description: str | None
    text: str


LocalMcpResourceItem = McpResourceItem
LocalMcpResourceReadResult = McpResourceReadResult


AI_FRONTIER_LOCAL_MCP_SERVER_ID = "ai_frontier_local"
AI_FRONTIER_LOCAL_MCP_SERVER_DISPLAY_NAME = "AI 前沿研究本地 MCP 服务"
AI_FRONTIER_STDIO_MCP_SERVER_ID = "ai_frontier_stdio"
AI_FRONTIER_STDIO_MCP_SERVER_DISPLAY_NAME = "AI 前沿研究进程外 MCP 服务"
AI_FRONTIER_EXTERNAL_MCP_SERVER_ID = "ai_frontier_external"
AI_FRONTIER_EXTERNAL_MCP_SERVER_DISPLAY_NAME = "AI 前沿研究外部 MCP 服务"

AI_FRONTIER_DIGEST_RESOURCE_ID = "ai.frontier.digest"
AI_FRONTIER_DIGEST_RESOURCE_URI = "ai-frontier://digest"
AI_FRONTIER_DIGEST_RESOURCE_DISPLAY_NAME = "AI 前沿摘要"

AI_FRONTIER_SEARCH_TOOL_NAME = "ai.frontier.search"
AI_FRONTIER_SEARCH_TOOL_DISPLAY_NAME = "AI 前沿搜索"

AI_FRONTIER_BRIEF_PROMPT_NAME = "ai.frontier.brief"
AI_FRONTIER_BRIEF_PROMPT_DISPLAY_NAME = "AI 前沿研究 Brief"
