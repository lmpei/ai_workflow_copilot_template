from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.models.ai_frontier_research_record import AiFrontierResearchRecord
from app.models.ai_hot_tracker_tracking_run import AiHotTrackerTrackingRun


AI_HOT_TRACKER_SOURCE_CATEGORIES = (
    "models",
    "products",
    "developer_tools",
    "research",
    "business",
    "open_source",
)

AI_HOT_TRACKER_LEGACY_CATEGORY_ALIASES = {
    "model_research": "research",
    "frameworks": "developer_tools",
    "inference_runtime": "developer_tools",
    "local_runtime": "developer_tools",
    "agent_frameworks": "developer_tools",
}

AiHotTrackerSourceKind = Literal["rss_feed", "atom_feed", "html_list"]
AiHotTrackerSourceParseMode = Literal["rss_feed", "atom_feed", "html_list"]
AiHotTrackerSourceFamily = Literal["official", "media", "research", "open_source"]
AiHotTrackerCadence = Literal["manual", "daily", "twice_daily", "weekly"]
AiHotTrackerRunTriggerKind = Literal["manual", "scheduled"]
AiHotTrackerRunStatus = Literal["completed", "degraded", "failed"]
AiHotTrackerPriorityLevel = Literal["high", "medium", "low"]
AiHotTrackerSignalConfidence = Literal["high", "medium", "low"]
AiHotTrackerChangeState = Literal[
    "first_run",
    "meaningful_update",
    "steady_state",
    "degraded",
    "failed",
]
AiHotTrackerSignalChangeType = Literal["new", "continuing", "cooling"]


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
    source_kind: Literal["official", "repository", "docs", "paper", "media", "other"] = "other"


class AiFrontierResearchOutput(BaseModel):
    frontier_summary: str
    trend_judgment: str
    themes: list[AiFrontierTheme] = Field(default_factory=list)
    events: list[AiFrontierEvent] = Field(default_factory=list)
    project_cards: list[AiFrontierProjectCard] = Field(default_factory=list)
    reference_sources: list[AiFrontierReferenceSource] = Field(default_factory=list)


class AiHotTrackerBriefSignal(BaseModel):
    title: str
    summary: str
    why_now: str
    impact: str = ""
    audience: list[str] = Field(default_factory=list)
    change_type: AiHotTrackerSignalChangeType = "continuing"
    priority_level: AiHotTrackerPriorityLevel = "medium"
    confidence: AiHotTrackerSignalConfidence = "medium"
    source_item_ids: list[str] = Field(default_factory=list)


class AiHotTrackerKeepWatchingItem(BaseModel):
    title: str
    reason: str
    source_item_ids: list[str] = Field(default_factory=list)


class AiHotTrackerReferenceSource(BaseModel):
    label: str
    url: str
    source_kind: Literal["official", "repository", "docs", "paper", "media", "other"] = "other"


class AiHotTrackerBriefOutput(BaseModel):
    headline: str
    summary: str
    change_state: AiHotTrackerChangeState = "first_run"
    signals: list[AiHotTrackerBriefSignal] = Field(default_factory=list)
    keep_watching: list[AiHotTrackerKeepWatchingItem] = Field(default_factory=list)
    blindspots: list[str] = Field(default_factory=list)
    reference_sources: list[AiHotTrackerReferenceSource] = Field(default_factory=list)


def build_default_ai_hot_tracker_brief_output() -> AiHotTrackerBriefOutput:
    return AiHotTrackerBriefOutput(
        headline="本轮暂时没有可用热点",
        summary="这一轮还没有形成可展示的热点简报。",
        change_state="degraded",
        signals=[],
        keep_watching=[],
        blindspots=[],
        reference_sources=[],
    )


class AiHotTrackerSourceDefinition(BaseModel):
    id: str
    label: str
    category: str
    source_family: AiHotTrackerSourceFamily = "official"
    source_kind: AiHotTrackerSourceKind
    parse_mode: AiHotTrackerSourceParseMode | None = None
    feed_url: str
    site_url: str | None = None
    tags: list[str] = Field(default_factory=list)
    audience_tags: list[str] = Field(default_factory=list)
    authority_weight: float = Field(default=0.5, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _fill_parse_mode(self) -> "AiHotTrackerSourceDefinition":
        if self.parse_mode is None:
            self.parse_mode = self.source_kind
        return self


class AiHotTrackerScoreBreakdown(BaseModel):
    novelty: float = 0.0
    freshness: float = 0.0
    authority: float = 0.0
    relevance: float = 0.0
    impact: float = 0.0


class AiHotTrackerSourceItem(BaseModel):
    id: str
    source_id: str
    source_label: str
    source_kind: AiHotTrackerSourceKind
    category: str
    source_family: AiHotTrackerSourceFamily = "official"
    title: str
    url: str
    summary: str
    published_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    audience_tags: list[str] = Field(default_factory=list)
    rank_score: float = 0.0
    score_breakdown: AiHotTrackerScoreBreakdown = Field(
        default_factory=AiHotTrackerScoreBreakdown
    )
    rank_reason: str = ""
    cluster_id: str | None = None
    event_id: str | None = None


class AiHotTrackerSourceFailure(BaseModel):
    source_id: str
    source_label: str
    message: str


class AiHotTrackerSignalCluster(BaseModel):
    cluster_id: str
    event_id: str
    title: str
    category: str
    representative_item_id: str
    source_item_ids: list[str] = Field(default_factory=list)
    source_labels: list[str] = Field(default_factory=list)
    rank_score: float = 0.0
    priority_level: AiHotTrackerPriorityLevel = "low"
    fingerprint: str
    is_new: bool = False
    is_continuing: bool = False
    is_cooling: bool = False


class AiHotTrackerClusterSnapshot(BaseModel):
    cluster_id: str
    event_id: str
    fingerprint: str
    title: str
    category: str
    representative_item_id: str | None = None
    rank_score: float = 0.0
    priority_level: AiHotTrackerPriorityLevel = "low"
    source_item_ids: list[str] = Field(default_factory=list)
    source_labels: list[str] = Field(default_factory=list)
    title_tokens: list[str] = Field(default_factory=list)
    version_tokens: list[str] = Field(default_factory=list)


class AiHotTrackerTrackingProfile(BaseModel):
    topic: str = "AI 模型、产品、工具、论文、开源与商业变化"
    scope: str = "从高可信来源持续追踪全球 AI 变化，筛选对大众 AI 用户真正值得关注的信号。"
    source_strategy: Literal["allowlist_curated"] = "allowlist_curated"
    enabled_categories: list[str] = Field(
        default_factory=lambda: list(AI_HOT_TRACKER_SOURCE_CATEGORIES)
    )
    cadence: AiHotTrackerCadence = "daily"
    alert_threshold: int = Field(default=1, ge=1, le=10)
    max_items_per_run: int = Field(default=24, ge=6, le=40)


def build_default_ai_hot_tracker_tracking_profile_config() -> dict[str, object]:
    return AiHotTrackerTrackingProfile().model_dump(mode="json")


def normalize_ai_hot_tracker_tracking_profile(
    value: dict[str, object] | None,
) -> AiHotTrackerTrackingProfile:
    payload = build_default_ai_hot_tracker_tracking_profile_config()
    if isinstance(value, dict):
        payload.update(value)

    profile = AiHotTrackerTrackingProfile.model_validate(payload)
    filtered_categories: list[str] = []
    for category in profile.enabled_categories:
        normalized_category = AI_HOT_TRACKER_LEGACY_CATEGORY_ALIASES.get(category, category)
        if normalized_category in AI_HOT_TRACKER_SOURCE_CATEGORIES:
            filtered_categories.append(normalized_category)

    return profile.model_copy(
        update={
            "enabled_categories": list(dict.fromkeys(filtered_categories))
            or list(AI_HOT_TRACKER_SOURCE_CATEGORIES),
        }
    )


def _build_legacy_brief_signal(
    *,
    title: str,
    summary: str,
    why_now: str,
    source_item_ids: list[str],
    priority_level: AiHotTrackerPriorityLevel = "medium",
) -> AiHotTrackerBriefSignal:
    return AiHotTrackerBriefSignal(
        title=title,
        summary=summary,
        why_now=why_now,
        impact=why_now,
        audience=["AI 用户"],
        change_type="continuing",
        priority_level=priority_level,
        confidence="medium",
        source_item_ids=source_item_ids,
    )


def _convert_legacy_frontier_output(
    output: AiFrontierResearchOutput,
) -> AiHotTrackerBriefOutput:
    signals: list[AiHotTrackerBriefSignal] = []
    seen_titles: set[str] = set()

    for event in output.events:
        if event.title in seen_titles:
            continue
        seen_titles.add(event.title)
        signals.append(
            _build_legacy_brief_signal(
                title=event.title,
                summary=event.summary,
                why_now=event.significance,
                source_item_ids=event.source_item_ids,
            )
        )

    for card in output.project_cards:
        if len(signals) >= 6 or card.title in seen_titles:
            continue
        seen_titles.add(card.title)
        signals.append(
            _build_legacy_brief_signal(
                title=card.title,
                summary=card.summary,
                why_now=card.why_it_matters,
                source_item_ids=card.source_item_ids,
            )
        )

    if not signals:
        for theme in output.themes[:3]:
            signals.append(
                _build_legacy_brief_signal(
                    title=theme.label,
                    summary=theme.summary,
                    why_now=theme.summary,
                    source_item_ids=[],
                    priority_level="low",
                )
            )

    keep_watching = [
        AiHotTrackerKeepWatchingItem(
            title=theme.label,
            reason=theme.summary,
            source_item_ids=[],
        )
        for theme in output.themes[:4]
    ]

    headline = signals[0].title if signals else "AI 热点追踪"

    return AiHotTrackerBriefOutput(
        headline=headline,
        summary=output.frontier_summary,
        change_state="meaningful_update",
        signals=signals[:6],
        keep_watching=keep_watching[:4],
        blindspots=[],
        reference_sources=[
            AiHotTrackerReferenceSource.model_validate(source.model_dump(mode="json"))
            for source in output.reference_sources
        ],
    )


def normalize_ai_hot_tracker_brief_output(
    value: dict[str, object] | AiHotTrackerBriefOutput | None,
) -> AiHotTrackerBriefOutput:
    if isinstance(value, AiHotTrackerBriefOutput):
        return value
    if not isinstance(value, dict):
        return build_default_ai_hot_tracker_brief_output()

    if "headline" in value and "signals" in value:
        return AiHotTrackerBriefOutput.model_validate(value)

    if "frontier_summary" in value and "trend_judgment" in value:
        legacy_output = AiFrontierResearchOutput.model_validate(value)
        return _convert_legacy_frontier_output(legacy_output)

    return build_default_ai_hot_tracker_brief_output()


class AiHotTrackerReportResponse(BaseModel):
    title: str
    question: str
    output: AiHotTrackerBriefOutput
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
    grounding_source_item_ids: list[str] = Field(default_factory=list)
    grounding_event_ids: list[str] = Field(default_factory=list)
    grounding_blindspots: list[str] = Field(default_factory=list)
    grounding_notes: list[str] = Field(default_factory=list)


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
    report_output: AiHotTrackerBriefOutput
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
    priority_level: AiHotTrackerPriorityLevel = "low"
    notify_reason: str | None = None
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


class AiHotTrackerTrackingStateResponse(BaseModel):
    workspace_id: str
    tracking_profile: AiHotTrackerTrackingProfile
    last_checked_at: datetime | None = None
    last_successful_scan_at: datetime | None = None
    next_due_at: datetime | None = None
    consecutive_failure_count: int = 0
    last_error_message: str | None = None
    latest_saved_run_id: str | None = None
    latest_saved_run_generated_at: datetime | None = None
    latest_change_state: AiHotTrackerChangeState | None = None
    latest_notify_reason: str | None = None
    latest_meaningful_update_at: datetime | None = None


class AiHotTrackerSignalMemoryRecord(BaseModel):
    event_id: str
    fingerprint: str
    title: str
    category: str
    first_seen_at: datetime
    last_seen_at: datetime
    continuity_state: Literal["new", "continuing", "cooling"] = "continuing"
    activity_state: Literal["heating", "continuing", "cooling", "replaced"] = "continuing"
    source_families: list[AiHotTrackerSourceFamily] = Field(default_factory=list)
    source_item_ids: list[str] = Field(default_factory=list)
    source_labels: list[str] = Field(default_factory=list)
    latest_priority_level: AiHotTrackerPriorityLevel = "low"
    latest_rank_score: float = 0.0
    last_seen_run_id: str | None = None
    streak_count: int = 0
    cooling_since: datetime | None = None
    superseded_by_event_id: str | None = None
    last_cluster_snapshot: dict[str, object] = Field(default_factory=dict)
    note: str | None = None


class AiHotTrackerAgentRoleTrace(BaseModel):
    role: Literal["scout", "resolver", "analyst", "editor", "evaluator", "follow_up"]
    summary: str
    status: Literal["completed", "degraded", "failed"] = "completed"
    details: dict[str, object] = Field(default_factory=dict)


class AiHotTrackerJudgmentFinding(BaseModel):
    code: str
    status: Literal["pass", "warn", "fail"]
    summary: str
    details: dict[str, object] = Field(default_factory=dict)


class AiHotTrackerRunEvaluationResponse(BaseModel):
    run_id: str
    ranked_items: list[AiHotTrackerSourceItem] = Field(default_factory=list)
    clustered_signals: list[AiHotTrackerSignalCluster] = Field(default_factory=list)
    event_memories: list[AiHotTrackerSignalMemoryRecord] = Field(default_factory=list)
    source_failures: list[AiHotTrackerSourceFailure] = Field(default_factory=list)
    output: AiHotTrackerBriefOutput = Field(
        default_factory=build_default_ai_hot_tracker_brief_output
    )
    delta: AiHotTrackerTrackingRunDelta
    agent_trace: list[AiHotTrackerAgentRoleTrace] = Field(default_factory=list)
    quality_checks: list[AiHotTrackerJudgmentFinding] = Field(default_factory=list)


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
    output: AiHotTrackerBriefOutput
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
            output=normalize_ai_hot_tracker_brief_output(run.output_json or {}),
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
                project_cards=[
                    AiFrontierProjectCard.model_validate(item) for item in record.project_cards_json
                ],
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
