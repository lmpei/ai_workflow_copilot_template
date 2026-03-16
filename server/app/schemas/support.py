from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.scenario import ScenarioEvidenceItem
from app.schemas.tool import SearchDocumentMatch, ToolDocumentSummary

SupportTaskType = Literal[
    "ticket_summary",
    "reply_draft",
]


class SupportTaskInput(BaseModel):
    customer_issue: str | None = None


class SupportArtifacts(BaseModel):
    document_count: int
    match_count: int
    documents: list[ToolDocumentSummary] = Field(default_factory=list)
    matches: list[SearchDocumentMatch] = Field(default_factory=list)
    tool_call_ids: list[str] = Field(default_factory=list)
    draft_reply: str | None = None


class SupportCopilotResult(BaseModel):
    module_type: Literal["support"] = "support"
    task_type: SupportTaskType
    title: str
    summary: str
    highlights: list[str] = Field(default_factory=list)
    evidence: list[ScenarioEvidenceItem] = Field(default_factory=list)
    artifacts: SupportArtifacts
    metadata: dict[str, object] = Field(default_factory=dict)
