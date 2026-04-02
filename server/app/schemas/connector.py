from datetime import datetime
from typing import Literal

from pydantic import BaseModel

WorkspaceConnectorConsentState = Literal["not_granted", "granted"]


class ConnectorDefinition(BaseModel):
    id: str
    display_name: str
    summary: str
    kind: Literal["external_context"]
    consent_scope: Literal["workspace"]
    module_types: list[str]
    requires_consent: bool = True
    pilot_status: Literal["bounded_pilot"] = "bounded_pilot"


class ConnectorConsentGrantRequest(BaseModel):
    consent_note: str | None = None


class WorkspaceConnectorStatusResponse(BaseModel):
    connector: ConnectorDefinition
    workspace_id: str
    consent_state: WorkspaceConnectorConsentState
    granted_by: str | None = None
    consent_note: str | None = None
    granted_at: datetime | None = None
    updated_at: datetime | None = None
