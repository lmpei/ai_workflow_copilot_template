from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.scenario import ScenarioEvidenceItem
from app.schemas.tool import SearchDocumentMatch, ToolDocumentSummary

ResearchTaskType = Literal[
    "research_summary",
    "workspace_report",
]


class ResearchTaskInput(BaseModel):
    goal: str | None = None


class ResearchArtifacts(BaseModel):
    document_count: int
    match_count: int
    documents: list[ToolDocumentSummary] = Field(default_factory=list)
    matches: list[SearchDocumentMatch] = Field(default_factory=list)
    tool_call_ids: list[str] = Field(default_factory=list)


class ResearchAssistantResult(BaseModel):
    module_type: Literal["research"] = "research"
    task_type: ResearchTaskType
    title: str
    summary: str
    highlights: list[str] = Field(default_factory=list)
    evidence: list[ScenarioEvidenceItem] = Field(default_factory=list)
    artifacts: ResearchArtifacts
    metadata: dict[str, object] = Field(default_factory=dict)
