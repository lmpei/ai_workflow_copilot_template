from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.ai_frontier_research_record import AiFrontierResearchRecord


class AiFrontierTheme(BaseModel):
    label: str
    summary: str


class AiFrontierEvent(BaseModel):
    title: str
    summary: str
    significance: str


class AiFrontierProjectCard(BaseModel):
    title: str
    source_label: str
    summary: str
    why_it_matters: str
    official_url: str | None = None
    repo_url: str | None = None
    docs_url: str | None = None
    tags: list[str] = Field(default_factory=list)


class AiFrontierReferenceSource(BaseModel):
    label: str
    url: str
    source_kind: Literal["official", "repository", "docs", "paper", "other"] = "other"


class AiFrontierResearchOutput(BaseModel):
    frontier_summary: str
    trend_judgment: str
    themes: list[AiFrontierTheme] = Field(default_factory=list)
    events: list[AiFrontierEvent] = Field(default_factory=list)
    project_cards: list[AiFrontierProjectCard] = Field(default_factory=list)
    reference_sources: list[AiFrontierReferenceSource] = Field(default_factory=list)


AiHotTrackerSourceKind = Literal["rss_feed", "atom_feed"]


class AiHotTrackerSourceDefinition(BaseModel):
    id: str
    label: str
    category: str
    source_kind: AiHotTrackerSourceKind
    feed_url: str
    site_url: str | None = None
    tags: list[str] = Field(default_factory=list)


class AiHotTrackerSourceItem(BaseModel):
    id: str
    source_id: str
    source_label: str
    source_kind: AiHotTrackerSourceKind
    category: str
    title: str
    url: str
    summary: str
    published_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)


class AiHotTrackerSourceFailure(BaseModel):
    source_id: str
    source_label: str
    message: str


class AiHotTrackerReportResponse(BaseModel):
    title: str
    question: str
    output: AiFrontierResearchOutput
    source_catalog: list[AiHotTrackerSourceDefinition] = Field(default_factory=list)
    source_items: list[AiHotTrackerSourceItem] = Field(default_factory=list)
    source_failures: list[AiHotTrackerSourceFailure] = Field(default_factory=list)
    source_set: dict[str, object] = Field(default_factory=dict)
    generated_at: datetime
    degraded_reason: str | None = None


class AiFrontierFollowUpEntry(BaseModel):
    question: str
    answer: str
    created_at: datetime | None = None


class AiFrontierResearchRecordWriteRequest(BaseModel):
    title: str | None = None
    question: str
    answer_text: str | None = None
    output: AiFrontierResearchOutput
    follow_ups: list[AiFrontierFollowUpEntry] = Field(default_factory=list)
    source_set: dict[str, object] = Field(default_factory=dict)
    conversation_id: str | None = None
    source_trace_id: str | None = None


class AiHotTrackerFollowUpRequest(BaseModel):
    report_question: str
    report_answer: str | None = None
    report_output: AiFrontierResearchOutput
    follow_up_question: str
    prior_follow_ups: list[AiFrontierFollowUpEntry] = Field(default_factory=list)
    source_set: dict[str, object] = Field(default_factory=dict)


class AiHotTrackerFollowUpResponse(BaseModel):
    answer: str
    follow_up: AiFrontierFollowUpEntry


class AiFrontierResearchRecordResponse(BaseModel):
    id: str
    workspace_id: str
    conversation_id: str | None = None
    source_run_id: str | None = None
    source_trace_id: str | None = None
    created_by: str
    title: str
    question: str
    answer_text: str | None = None
    output: AiFrontierResearchOutput
    follow_ups: list[AiFrontierFollowUpEntry] = Field(default_factory=list)
    source_set: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, record: AiFrontierResearchRecord) -> "AiFrontierResearchRecordResponse":
        source_set = record.source_set_json or {}
        answer_text = source_set.get("answer_text")
        follow_ups = source_set.get("follow_ups")
        if not isinstance(follow_ups, list):
            raise ValueError("Persisted AI hot tracker record follow_ups must be a list")
        return cls(
            id=record.id,
            workspace_id=record.workspace_id,
            conversation_id=record.conversation_id,
            source_run_id=record.source_run_id,
            source_trace_id=record.source_trace_id,
            created_by=record.created_by,
            title=record.title,
            question=record.question,
            answer_text=answer_text if isinstance(answer_text, str) else None,
            output=AiFrontierResearchOutput(
                frontier_summary=record.frontier_summary,
                trend_judgment=record.trend_judgment,
                themes=[AiFrontierTheme.model_validate(item) for item in record.themes_json],
                events=[AiFrontierEvent.model_validate(item) for item in record.events_json],
                project_cards=[AiFrontierProjectCard.model_validate(item) for item in record.project_cards_json],
                reference_sources=[
                    AiFrontierReferenceSource.model_validate(item)
                    for item in record.reference_sources_json
                ],
            ),
            follow_ups=[
                AiFrontierFollowUpEntry.model_validate(item)
                for item in follow_ups
                if isinstance(item, dict)
            ],
            source_set=source_set,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
