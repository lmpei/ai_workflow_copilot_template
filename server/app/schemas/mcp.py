from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel

from app.schemas.connector import WorkspaceConnectorStatusResponse


class McpServerDefinition(BaseModel):
    id: str
    display_name: str
    summary: str
    transport: Literal["local_inproc"]
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


@dataclass(frozen=True, slots=True)
class LocalMcpResourceReadResult:
    server: McpServerDefinition
    resource: McpResourceDefinition
    text: str
    resource_count: int
