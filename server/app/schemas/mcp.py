from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.connector import WorkspaceConnectorStatusResponse

McpTransportKind = Literal["local_inproc", "stdio_process"]
RemoteMcpReadStatus = Literal[
    "consent_required",
    "consent_revoked",
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
    pilot_status: Literal["bounded_pilot"] = "bounded_pilot"


class McpResourceDefinition(BaseModel):
    id: str
    uri: str
    display_name: str
    summary: str
    mime_type: Literal["text/markdown"]
    module_types: list[str]
    connector_id: str
    resource_kind: Literal["resource"] = "resource"
    pilot_status: Literal["bounded_pilot"] = "bounded_pilot"


class WorkspaceConnectorMcpStatusResponse(BaseModel):
    connector_status: WorkspaceConnectorStatusResponse
    server: McpServerDefinition
    resources: list[McpResourceDefinition]


class McpStdioServerConfig(BaseModel):
    transport: Literal["stdio_process"] = "stdio_process"
    launch_kind: Literal["python_module"] = "python_module"
    module: str
    args: list[str] = Field(default_factory=list)
    working_directory: str
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


LocalMcpResourceItem = McpResourceItem
LocalMcpResourceReadResult = McpResourceReadResult


RESEARCH_CONTEXT_LOCAL_MCP_SERVER_ID = "research_context_local"
RESEARCH_CONTEXT_LOCAL_MCP_SERVER_DISPLAY_NAME = "Research 本地 MCP 服务"
RESEARCH_CONTEXT_STDIO_MCP_SERVER_ID = "research_context_stdio"
RESEARCH_CONTEXT_STDIO_MCP_SERVER_DISPLAY_NAME = "Research 进程外 MCP 服务"
RESEARCH_CONTEXT_DIGEST_RESOURCE_ID = "research.context.digest"
RESEARCH_CONTEXT_DIGEST_RESOURCE_URI = "resource://research.context.digest"
RESEARCH_CONTEXT_DIGEST_RESOURCE_DISPLAY_NAME = "Research 外部上下文摘要"
