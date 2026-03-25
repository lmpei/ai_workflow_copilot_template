from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.scenario import ScenarioEvidenceItem
from app.schemas.tool import SearchDocumentMatch, ToolDocumentSummary

SupportTaskType = Literal[
    "ticket_summary",
    "reply_draft",
]
SupportSeverity = Literal[
    "low",
    "medium",
    "high",
    "critical",
]
SupportEvidenceStatus = Literal[
    "grounded_matches",
    "documents_only",
    "no_documents",
]


class SupportTaskInput(BaseModel):
    customer_issue: str | None = None
    product_area: str | None = None
    severity: SupportSeverity | None = None
    desired_outcome: str | None = None
    reproduction_steps: list[str] = Field(default_factory=list)


class SupportCaseBrief(BaseModel):
    issue_summary: str
    product_area: str | None = None
    severity: SupportSeverity | None = None
    desired_outcome: str | None = None
    reproduction_steps: list[str] = Field(default_factory=list)
    evidence_status: SupportEvidenceStatus


class SupportFinding(BaseModel):
    title: str
    summary: str
    evidence_ref_ids: list[str] = Field(default_factory=list)


class SupportTriageDecision(BaseModel):
    evidence_status: SupportEvidenceStatus
    needs_manual_review: bool
    should_escalate: bool
    recommended_owner: str
    rationale: str


class SupportReplyDraft(BaseModel):
    subject_line: str
    body: str
    confidence_note: str


class SupportArtifacts(BaseModel):
    document_count: int
    match_count: int
    documents: list[ToolDocumentSummary] = Field(default_factory=list)
    matches: list[SearchDocumentMatch] = Field(default_factory=list)
    tool_call_ids: list[str] = Field(default_factory=list)
    evidence_status: SupportEvidenceStatus


class SupportCopilotResult(BaseModel):
    module_type: Literal["support"] = "support"
    task_type: SupportTaskType
    title: str
    input: SupportTaskInput = Field(default_factory=SupportTaskInput)
    case_brief: SupportCaseBrief
    findings: list[SupportFinding] = Field(default_factory=list)
    triage: SupportTriageDecision
    open_questions: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    reply_draft: SupportReplyDraft | None = None
    summary: str
    highlights: list[str] = Field(default_factory=list)
    evidence: list[ScenarioEvidenceItem] = Field(default_factory=list)
    artifacts: SupportArtifacts
    metadata: dict[str, object] = Field(default_factory=dict)
