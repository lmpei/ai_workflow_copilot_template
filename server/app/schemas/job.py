from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.scenario import ScenarioEvidenceItem
from app.schemas.tool import SearchDocumentMatch, ToolDocumentSummary

JobTaskType = Literal[
    "jd_summary",
    "resume_match",
]


class JobTaskInput(BaseModel):
    target_role: str | None = None


class JobArtifacts(BaseModel):
    document_count: int
    match_count: int
    documents: list[ToolDocumentSummary] = Field(default_factory=list)
    matches: list[SearchDocumentMatch] = Field(default_factory=list)
    tool_call_ids: list[str] = Field(default_factory=list)
    fit_signal: str | None = None
    recommended_next_step: str | None = None


class JobAssistantResult(BaseModel):
    module_type: Literal["job"] = "job"
    task_type: JobTaskType
    title: str
    summary: str
    highlights: list[str] = Field(default_factory=list)
    evidence: list[ScenarioEvidenceItem] = Field(default_factory=list)
    artifacts: JobArtifacts
    metadata: dict[str, object] = Field(default_factory=dict)
