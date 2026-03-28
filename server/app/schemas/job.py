from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.scenario import ScenarioEvidenceItem
from app.schemas.tool import SearchDocumentMatch, ToolDocumentSummary

JobTaskType = Literal[
    "jd_summary",
    "resume_match",
]
JobEvidenceStatus = Literal[
    "grounded_matches",
    "documents_only",
    "no_documents",
]
JobFitSignal = Literal[
    "grounded_match_found",
    "role_requirements_grounded",
    "insufficient_grounding",
    "no_documents_available",
]
JobHiringPacketStatus = Literal[
    "collecting_materials",
    "needs_alignment",
    "review_ready",
    "shortlist_ready",
]


class JobTaskInput(BaseModel):
    target_role: str | None = None
    candidate_label: str | None = None
    seniority: str | None = None
    must_have_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    hiring_context: str | None = None
    comparison_task_ids: list[str] = Field(default_factory=list)
    comparison_notes: str | None = None


class JobReviewBrief(BaseModel):
    role_summary: str
    candidate_label: str | None = None
    seniority: str | None = None
    must_have_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    hiring_context: str | None = None
    evidence_status: JobEvidenceStatus
    comparison_task_count: int = 0


class JobFinding(BaseModel):
    title: str
    summary: str
    evidence_ref_ids: list[str] = Field(default_factory=list)


class JobFitAssessment(BaseModel):
    fit_signal: JobFitSignal
    evidence_status: JobEvidenceStatus
    recommended_outcome: str
    confidence_note: str
    rationale: str


class JobComparisonCandidate(BaseModel):
    task_id: str
    task_type: JobTaskType
    candidate_label: str
    title: str
    summary: str
    target_role: str | None = None
    seniority: str | None = None
    fit_signal: JobFitSignal
    evidence_status: JobEvidenceStatus
    recommended_outcome: str | None = None
    findings: list[JobFinding] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
    evidence_ref_ids: list[str] = Field(default_factory=list)


class JobShortlistEntry(BaseModel):
    rank: int
    task_id: str
    candidate_label: str
    fit_signal: JobFitSignal
    evidence_status: JobEvidenceStatus
    recommendation: str
    rationale: str
    risks: list[str] = Field(default_factory=list)
    interview_focus: list[str] = Field(default_factory=list)
    evidence_ref_ids: list[str] = Field(default_factory=list)


class JobShortlistResult(BaseModel):
    comparison_task_ids: list[str] = Field(default_factory=list)
    comparison_notes: str | None = None
    shortlist_summary: str
    entries: list[JobShortlistEntry] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    interview_focus: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)


class JobArtifacts(BaseModel):
    document_count: int
    match_count: int
    documents: list[ToolDocumentSummary] = Field(default_factory=list)
    matches: list[SearchDocumentMatch] = Field(default_factory=list)
    tool_call_ids: list[str] = Field(default_factory=list)
    evidence_status: JobEvidenceStatus
    fit_signal: JobFitSignal
    recommended_next_step: str


class JobHiringPacketLink(BaseModel):
    packet_id: str
    event_id: str
    packet_status: JobHiringPacketStatus


class JobHiringPacketActionLoop(BaseModel):
    can_continue: bool
    suggested_task_type: JobTaskType
    comparison_mode: bool = False
    status_guidance: str
    suggested_note_prompt: str | None = None


class JobAssistantResult(BaseModel):
    module_type: Literal["job"] = "job"
    task_type: JobTaskType
    title: str
    input: JobTaskInput = Field(default_factory=JobTaskInput)
    review_brief: JobReviewBrief
    findings: list[JobFinding] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    assessment: JobFitAssessment
    comparison_candidates: list[JobComparisonCandidate] = Field(default_factory=list)
    shortlist: JobShortlistResult | None = None
    open_questions: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    summary: str
    highlights: list[str] = Field(default_factory=list)
    evidence: list[ScenarioEvidenceItem] = Field(default_factory=list)
    artifacts: JobArtifacts
    metadata: dict[str, object] = Field(default_factory=dict)


class JobHiringPacketEventResponse(BaseModel):
    id: str
    job_hiring_packet_id: str
    task_id: str
    task_type: JobTaskType
    event_kind: str
    title: str
    summary: str
    packet_status: JobHiringPacketStatus
    candidate_label: str | None = None
    target_role: str | None = None
    fit_signal: JobFitSignal | None = None
    evidence_status: JobEvidenceStatus | None = None
    recommended_outcome: str | None = None
    comparison_task_ids: list[str] = Field(default_factory=list)
    shortlist_entry_count: int = 0
    created_at: str


class JobHiringPacketSummaryResponse(BaseModel):
    id: str
    workspace_id: str
    created_by: str
    title: str
    status: JobHiringPacketStatus
    action_loop: JobHiringPacketActionLoop
    target_role: str | None = None
    seniority: str | None = None
    latest_task_id: str | None = None
    latest_task_type: JobTaskType
    latest_summary: str
    latest_review_brief: JobReviewBrief
    latest_assessment: JobFitAssessment
    latest_shortlist: JobShortlistResult | None = None
    latest_next_steps: list[str] = Field(default_factory=list)
    latest_candidate_labels: list[str] = Field(default_factory=list)
    latest_packet_note: str | None = None
    latest_recommended_outcome: str | None = None
    latest_evidence_status: JobEvidenceStatus | None = None
    latest_fit_signal: JobFitSignal | None = None
    comparison_history_count: int = 0
    event_count: int = 0
    created_at: str
    updated_at: str


class JobHiringPacketResponse(JobHiringPacketSummaryResponse):
    events: list[JobHiringPacketEventResponse] = Field(default_factory=list)
