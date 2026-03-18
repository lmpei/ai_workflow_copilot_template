from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.scenario import ScenarioEvidenceItem
from app.schemas.tool import SearchDocumentMatch, ToolDocumentSummary

ResearchTaskType = Literal[
    "research_summary",
    "workspace_report",
]
ResearchDeliverable = Literal[
    "brief",
    "report",
]
ResearchRequestedSection = Literal[
    "summary",
    "findings",
    "evidence",
    "open_questions",
    "next_steps",
]


class ResearchTaskInput(BaseModel):
    goal: str | None = None
    focus_areas: list[str] = Field(default_factory=list)
    key_questions: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    deliverable: ResearchDeliverable | None = None
    requested_sections: list[ResearchRequestedSection] = Field(default_factory=list)


class ResearchFinding(BaseModel):
    title: str
    summary: str
    evidence_ref_ids: list[str] = Field(default_factory=list)


class ResearchResultSections(BaseModel):
    summary: str
    findings: list[ResearchFinding] = Field(default_factory=list)
    evidence_overview: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


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
    input: ResearchTaskInput = Field(default_factory=ResearchTaskInput)
    summary: str
    sections: ResearchResultSections
    highlights: list[str] = Field(default_factory=list)
    evidence: list[ScenarioEvidenceItem] = Field(default_factory=list)
    artifacts: ResearchArtifacts
    metadata: dict[str, object] = Field(default_factory=dict)
