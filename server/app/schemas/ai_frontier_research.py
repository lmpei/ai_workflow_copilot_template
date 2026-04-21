from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.ai_frontier_research_record import AiFrontierResearchRecord
from app.models.ai_hot_tracker_tracking_run import AiHotTrackerTrackingRun


AI_HOT_TRACKER_SOURCE_CATEGORIES = (
    "model_research",
    "frameworks",
    "inference_runtime",
    "local_runtime",
    "agent_frameworks",
)

AiHotTrackerSourceKind = Literal["rss_feed", "atom_feed"]
AiHotTrackerCadence = Literal["manual", "daily", "twice_daily", "weekly"]
AiHotTrackerRunTriggerKind = Literal["manual", "scheduled"]
AiHotTrackerRunStatus = Literal["completed", "degraded", "failed"]
AiHotTrackerChangeState = Literal["first_run", "meaningful_update", "steady_state", "degraded"]


class AiFrontierTheme(BaseModel):
    label: str
    summary: str


class AiFrontierEvent(BaseModel):
    title: str
    summary: str
    significance: str
    source_item_ids: list[str] = Field(default_factory=list)


class AiFrontierProjectCard(BaseModel):
    title: str
    source_label: str
    summary: str
    why_it_matters: str
    official_url: str | None = None
    repo_url: str | None = None
    docs_url: str | None = None
    tags: list[str] = Field(default_factory=list)
    source_item_ids: list[str] = Field(default_factory=list)


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


class AiHotTrackerTrackingProfile(BaseModel):
    topic: str = "AI 模型、产品、开源与工程生态"
    scope: str = "围绕高可信来源持续追踪模型、产品、开源项目与工程生态变化。"
    enabled_categories: list[str] = Field(
        default_factory=lambda: list(AI_HOT_TRACKER_SOURCE_CATEGORIES)
    )
    cadence: AiHotTrackerCadence = "daily"
    alert_threshold: int = Field(default=1, ge=1, le=10)
    max_items_per_run: int = Field(default=18, ge=6, le=30)


def build_default_ai_hot_tracker_tracking_profile_config() -> dict[str, object]:
    return AiHotTrackerTrackingProfile().model_dump(mode="json")


def normalize_ai_hot_tracker_tracking_profile(
    value: dict[str, object] | None,
) -> AiHotTrackerTrackingProfile:
    payload = build_default_ai_hot_tracker_tracking_profile_config()
    if isinstance(value, dict):
        payload.update(value)

    profile = AiHotTrackerTrackingProfile.model_validate(payload)
    filtered_categories = [
        category
        for category in profile.enabled_categories
        if category in AI_HOT_TRACKER_SOURCE_CATEGORIES
    ]
    return profile.model_copy(
        update={
            "enabled_categories": filtered_categories or list(AI_HOT_TRACKER_SOURCE_CATEGORIES),
        }
    )


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


class AiHotTrackerTrackingRunDelta(BaseModel):
    previous_run_id: str | None = None
    change_state: AiHotTrackerChangeState = "first_run"
    summary: str
    should_notify: bool = True
    new_item_count: int = 0
    continuing_item_count: int = 0
    cooled_down_item_count: int = 0
    new_titles: list[str] = Field(default_factory=list)
    continuing_titles: list[str] = Field(default_factory=list)
    cooled_down_titles: list[str] = Field(default_factory=list)


class AiHotTrackerTrackingRunCreateRequest(BaseModel):
    trigger_kind: AiHotTrackerRunTriggerKind = "manual"


class AiHotTrackerTrackingRunFollowUpRequest(BaseModel):
    question: str
    focus_label: str | None = None
    focus_context: str | None = None


class AiHotTrackerTrackingRunFollowUpResponse(BaseModel):
    answer: str
    follow_up: AiFrontierFollowUpEntry


class AiHotTrackerTrackingRunResponse(BaseModel):
    id: str
    workspace_id: str
    previous_run_id: str | None = None
    created_by: str
    trigger_kind: AiHotTrackerRunTriggerKind
    status: AiHotTrackerRunStatus
    title: str
    question: str
    profile: AiHotTrackerTrackingProfile
    output: AiFrontierResearchOutput
    source_catalog: list[AiHotTrackerSourceDefinition] = Field(default_factory=list)
    source_items: list[AiHotTrackerSourceItem] = Field(default_factory=list)
    source_failures: list[AiHotTrackerSourceFailure] = Field(default_factory=list)
    source_set: dict[str, object] = Field(default_factory=dict)
    delta: AiHotTrackerTrackingRunDelta
    follow_ups: list[AiFrontierFollowUpEntry] = Field(default_factory=list)
    degraded_reason: str | None = None
    error_message: str | None = None
    generated_at: datetime
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, run: AiHotTrackerTrackingRun) -> "AiHotTrackerTrackingRunResponse":
        source_catalog = run.source_catalog_json if isinstance(run.source_catalog_json, list) else []
        source_items = run.source_items_json if isinstance(run.source_items_json, list) else []
        source_failures = run.source_failures_json if isinstance(run.source_failures_json, list) else []
        follow_ups = run.follow_ups_json if isinstance(run.follow_ups_json, list) else []
        return cls(
            id=run.id,
            workspace_id=run.workspace_id,
            previous_run_id=run.previous_run_id,
            created_by=run.created_by,
            trigger_kind=run.trigger_kind,
            status=run.status,
            title=run.title,
            question=run.question,
            profile=normalize_ai_hot_tracker_tracking_profile(run.profile_snapshot_json),
            output=AiFrontierResearchOutput.model_validate(run.output_json or {}),
            source_catalog=[
                AiHotTrackerSourceDefinition.model_validate(item)
                for item in source_catalog
                if isinstance(item, dict)
            ],
            source_items=[
                AiHotTrackerSourceItem.model_validate(item)
                for item in source_items
                if isinstance(item, dict)
            ],
            source_failures=[
                AiHotTrackerSourceFailure.model_validate(item)
                for item in source_failures
                if isinstance(item, dict)
            ],
            source_set=run.source_set_json or {},
            delta=AiHotTrackerTrackingRunDelta.model_validate(run.delta_json or {}),
            follow_ups=[
                AiFrontierFollowUpEntry.model_validate(item)
                for item in follow_ups
                if isinstance(item, dict)
            ],
            degraded_reason=run.degraded_reason,
            error_message=run.error_message,
            generated_at=run.generated_at,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )


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
