import json
from datetime import UTC, datetime

from pydantic import BaseModel, Field, ValidationError

from app.repositories import workspace_repository
from app.schemas.ai_frontier_research import (
    AiHotTrackerBriefOutput,
    AiHotTrackerBriefSignal,
    AiHotTrackerKeepWatchingItem,
    AiHotTrackerReferenceSource,
    AiHotTrackerReportResponse,
    AiHotTrackerSignalChangeType,
    AiHotTrackerSignalCluster,
    AiHotTrackerSourceItem,
    AiHotTrackerTrackingProfile,
    normalize_ai_hot_tracker_tracking_profile,
)
from app.services.ai_hot_tracker_decision_service import (
    AiHotTrackerDecisionResult,
    build_signal_decision_result,
)
from app.services.ai_hot_tracker_source_service import (
    AiHotTrackerSourceIntakeResult,
    fetch_ai_hot_tracker_source_items,
)
from app.services.model_interface_service import ModelInterfaceError, ModelMessage
from app.services.retrieval_generation_service import get_chat_model_interface

REPORT_SOURCE_SUMMARY_LIMIT = 240


class AiHotTrackerReportGenerationError(Exception):
    pass


class AiHotTrackerReportAccessError(Exception):
    pass


class _DraftSignal(BaseModel):
    title: str
    summary: str
    why_now: str
    impact: str
    audience: list[str] = Field(default_factory=list)
    change_type: AiHotTrackerSignalChangeType = "continuing"
    priority_level: str = "medium"
    confidence: str = "medium"
    source_item_ids: list[str] = Field(default_factory=list)


class _DraftKeepWatching(BaseModel):
    title: str
    reason: str
    source_item_ids: list[str] = Field(default_factory=list)


class _DraftBrief(BaseModel):
    headline: str
    summary: str
    change_state: str = "meaningful_update"
    signals: list[_DraftSignal] = Field(default_factory=list)
    keep_watching: list[_DraftKeepWatching] = Field(default_factory=list)
    blindspots: list[str] = Field(default_factory=list)


def build_ai_hot_tracker_internal_question(profile: AiHotTrackerTrackingProfile) -> str:
    return f"围绕“{profile.topic}”生成本轮 AI 热点判断简报。"


def filter_ai_hot_tracker_source_intake(
    *,
    intake: AiHotTrackerSourceIntakeResult,
    tracking_profile: AiHotTrackerTrackingProfile,
) -> AiHotTrackerSourceIntakeResult:
    allowed_categories = set(tracking_profile.enabled_categories)
    if not allowed_categories:
        return intake

    filtered_catalog = [
        source for source in intake.source_catalog if source.category in allowed_categories
    ]
    allowed_source_ids = {source.id for source in filtered_catalog}

    return AiHotTrackerSourceIntakeResult(
        source_catalog=filtered_catalog,
        source_items=[
            item
            for item in intake.source_items
            if item.source_id in allowed_source_ids and item.category in allowed_categories
        ],
        source_failures=[
            failure for failure in intake.source_failures if failure.source_id in allowed_source_ids
        ],
    )


def generate_ai_hot_tracker_report(*, workspace_id: str, user_id: str) -> AiHotTrackerReportResponse:
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise AiHotTrackerReportAccessError("Workspace not found")
    if workspace.module_type != "research":
        raise AiHotTrackerReportAccessError("AI hot tracker is only available in research workspaces")

    module_config = workspace.module_config_json if isinstance(workspace.module_config_json, dict) else {}
    tracking_profile = normalize_ai_hot_tracker_tracking_profile(
        module_config.get("tracking_profile") if isinstance(module_config.get("tracking_profile"), dict) else None
    )
    intake = filter_ai_hot_tracker_source_intake(
        intake=fetch_ai_hot_tracker_source_items(total_limit=tracking_profile.max_items_per_run),
        tracking_profile=tracking_profile,
    )
    return generate_ai_hot_tracker_report_from_intake(
        intake=intake,
        tracking_profile=tracking_profile,
    )


def generate_ai_hot_tracker_report_from_intake(
    *,
    intake: AiHotTrackerSourceIntakeResult,
    tracking_profile: AiHotTrackerTrackingProfile,
    decision_result: AiHotTrackerDecisionResult | None = None,
    generated_at: datetime | None = None,
) -> AiHotTrackerReportResponse:
    final_generated_at = generated_at or datetime.now(UTC)
    question = build_ai_hot_tracker_internal_question(tracking_profile)

    resolved_decision_result = decision_result or build_signal_decision_result(
        source_catalog=intake.source_catalog,
        source_items=intake.source_items,
        tracking_profile=tracking_profile,
        previous_snapshot=None,
        reference_time=final_generated_at,
    )

    if not intake.source_items:
        return _build_degraded_report(
            intake=intake,
            tracking_profile=tracking_profile,
            generated_at=final_generated_at,
            decision_result=resolved_decision_result,
            degraded_reason="source_intake_unavailable",
            headline="本轮暂时没有可用热点",
            summary="这次没有拿到足够有效的来源，因此还不能形成可信的热点判断。",
            keep_watching_reason="先不下结论，建议稍后重新获取，等待高可信来源恢复。",
        )

    if not resolved_decision_result.candidate_clusters:
        return _build_degraded_report(
            intake=intake,
            tracking_profile=tracking_profile,
            generated_at=final_generated_at,
            decision_result=resolved_decision_result,
            degraded_reason="report_candidates_unavailable",
            headline="本轮热点暂不明确",
            summary="来源已经更新，但还没有形成足够清晰、值得进入简报的主信号。",
            keep_watching_reason="这个方向仍在变化，建议继续观察后续来源再判断。",
        )

    try:
        draft = _generate_report_draft(
            source_items=resolved_decision_result.source_items,
            signal_clusters=resolved_decision_result.candidate_clusters,
            tracking_profile=tracking_profile,
            question=question,
        )
    except AiHotTrackerReportGenerationError:
        return _build_degraded_report(
            intake=intake,
            tracking_profile=tracking_profile,
            generated_at=final_generated_at,
            decision_result=resolved_decision_result,
            degraded_reason="report_generation_failed",
            headline="本轮简报暂未生成",
            summary="来源已经更新，但结构化简报还没有成功生成。这一轮暂时不作为正式判断使用。",
            keep_watching_reason="候选信号已经更新，建议稍后重新获取，等待简报生成恢复。",
        )

    output = _materialize_output(
        draft=draft,
        source_items=resolved_decision_result.source_items,
        signal_clusters=resolved_decision_result.signal_clusters,
    )
    headline = draft.headline.strip() or _fallback_headline(output, final_generated_at)
    output = output.model_copy(update={"headline": headline})

    return AiHotTrackerReportResponse(
        title=headline,
        question=question,
        output=output,
        source_catalog=intake.source_catalog,
        source_items=resolved_decision_result.source_items,
        source_failures=intake.source_failures,
        source_set=_build_source_set(
            intake=intake,
            tracking_profile=tracking_profile,
            generated_at=final_generated_at,
            question=question,
            decision_result=resolved_decision_result,
        ),
        generated_at=final_generated_at,
        degraded_reason=None,
    )


def _generate_report_draft(
    *,
    source_items: list[AiHotTrackerSourceItem],
    signal_clusters: list[AiHotTrackerSignalCluster],
    tracking_profile: AiHotTrackerTrackingProfile,
    question: str,
) -> _DraftBrief:
    interface = get_chat_model_interface()
    cluster_payload = _build_cluster_payload(
        signal_clusters=signal_clusters,
        source_items=source_items,
    )
    messages = _build_generation_messages(
        cluster_payload=cluster_payload,
        tracking_profile=tracking_profile,
        question=question,
    )

    last_model_error: ModelInterfaceError | None = None
    for _ in range(2):
        try:
            response = interface.generate_json_object(
                messages=messages,
                temperature=0.1,
                timeout=90.0,
            )
            try:
                return _DraftBrief.model_validate(response.data)
            except ValidationError as validation_error:
                return _repair_report_draft(
                    interface=interface,
                    cluster_payload=cluster_payload,
                    invalid_data=response.data,
                    validation_error=validation_error,
                    tracking_profile=tracking_profile,
                )
        except ModelInterfaceError as error:
            last_model_error = error

    raise AiHotTrackerReportGenerationError("Failed to generate AI hot tracker brief draft") from last_model_error


def _repair_report_draft(
    *,
    interface,
    cluster_payload: list[dict[str, object]],
    invalid_data: dict[str, object],
    validation_error: ValidationError,
    tracking_profile: AiHotTrackerTrackingProfile,
) -> _DraftBrief:
    messages = [
        ModelMessage(
            role="system",
            content=(
                "你是 JSON 修复器。只把已有 JSON 修成目标 schema，不补充外部事实。"
                " 只输出合法 JSON object，不输出 Markdown。"
            ),
        ),
        ModelMessage(
            role="user",
            content=(
                f"追踪主题：{tracking_profile.topic}\n"
                f"追踪范围：{tracking_profile.scope}\n"
                "请修复下面这份不合法的 JSON。\n"
                "必须保留字段：headline, summary, change_state, signals, keep_watching, blindspots。\n"
                "signals 每项必须包含：title, summary, why_now, impact, audience, change_type, priority_level, confidence, source_item_ids。\n"
                "keep_watching 每项必须包含：title, reason, source_item_ids。\n"
                "change_type 只能是 new, continuing, cooling。\n"
                "priority_level 只能是 high, medium, low。\n"
                "confidence 只能是 high, medium, low。\n"
                "signals 最多 6 项，keep_watching 最多 4 项，blindspots 最多 3 项。\n"
                f"\n候选信号：\n{json.dumps(cluster_payload, ensure_ascii=False)}"
                f"\n\n上一版 JSON：\n{json.dumps(invalid_data, ensure_ascii=False)}"
                f"\n\n校验错误：\n{validation_error.json()}"
            ),
        ),
    ]

    try:
        response = interface.generate_json_object(
            messages=messages,
            temperature=0.0,
            timeout=90.0,
        )
        return _DraftBrief.model_validate(response.data)
    except (ModelInterfaceError, ValidationError) as error:
        raise AiHotTrackerReportGenerationError("Failed to repair AI hot tracker brief draft") from error


def _build_cluster_payload(
    *,
    signal_clusters: list[AiHotTrackerSignalCluster],
    source_items: list[AiHotTrackerSourceItem],
) -> list[dict[str, object]]:
    item_map = {item.id: item for item in source_items}
    payload: list[dict[str, object]] = []
    for cluster in signal_clusters:
        representative = item_map.get(cluster.representative_item_id)
        payload.append(
            {
                "cluster_id": cluster.cluster_id,
                "event_id": cluster.event_id,
                "title": cluster.title,
                "category": cluster.category,
                "priority_level": cluster.priority_level,
                "rank_score": cluster.rank_score,
                "change_flags": {
                    "is_new": cluster.is_new,
                    "is_continuing": cluster.is_continuing,
                    "is_cooling": cluster.is_cooling,
                },
                "source_labels": cluster.source_labels,
                "source_item_ids": cluster.source_item_ids,
                "representative_item": _build_item_payload(representative) if representative else None,
                "supporting_items": [
                    _build_item_payload(item)
                    for item_id in cluster.source_item_ids
                    for item in [item_map.get(item_id)]
                    if item is not None
                ],
            }
        )
    return payload


def _build_item_payload(item: AiHotTrackerSourceItem | None) -> dict[str, object]:
    if item is None:
        return {}
    return {
        "id": item.id,
        "source": item.source_label,
        "source_family": item.source_family,
        "category": item.category,
        "title": item.title,
        "summary": item.summary[:REPORT_SOURCE_SUMMARY_LIMIT],
        "url": item.url,
        "published_at": item.published_at.isoformat() if item.published_at else None,
        "tags": item.tags,
        "audience_tags": item.audience_tags,
        "rank_reason": item.rank_reason,
        "score_breakdown": item.score_breakdown.model_dump(mode="json"),
    }


def _build_generation_messages(
    *,
    cluster_payload: list[dict[str, object]],
    tracking_profile: AiHotTrackerTrackingProfile,
    question: str,
) -> list[ModelMessage]:
    return [
        ModelMessage(
            role="system",
            content=(
                "你是面向大众 AI 用户的热点判断简报编辑。"
                " 你只能基于提供的候选信号和来源生成结论，不得引入未提供的外部事实。"
                " 你的目标不是复述新闻，而是帮助用户判断什么值得关注、为什么重要、适合谁关注。"
                " 表达要易懂但专业，避免内部技术词和系统实现说明。"
                " 如果证据不足，就主动收窄结论。只输出一个合法 JSON object。"
            ),
        ),
        ModelMessage(
            role="user",
            content=(
                f"追踪主题：{tracking_profile.topic}\n"
                f"追踪范围：{tracking_profile.scope}\n"
                f"本轮任务：{question}\n\n"
                "请基于下面的候选信号生成结构化判断型简报。\n"
                "必须输出字段：headline, summary, change_state, signals, keep_watching, blindspots。\n"
                "- headline：本轮标题，直接可展示。\n"
                "- summary：一段总括判断，说明这轮最值得关注的变化。\n"
                "- change_state：只能是 first_run, meaningful_update, steady_state, degraded, failed。\n"
                "- signals：3 到 6 个主信号，每项包含 title, summary, why_now, impact, audience, change_type, priority_level, confidence, source_item_ids。\n"
                "- impact：用一句话说清这件事会怎样影响普通 AI 用户、学习者、产品人或开发者。\n"
                "- audience：数组，写适合关注的人群，例如 AI 用户、学习者、产品人、开发者、创业者。\n"
                "- confidence：只能是 high, medium, low，用来表达当前判断把握。\n"
                "- keep_watching：2 到 4 个继续观察项，每项包含 title, reason, source_item_ids。\n"
                "- blindspots：1 到 3 个当前仍看不清、还缺什么证据、下轮要重点确认什么。\n"
                "- change_type 只能是 new, continuing, cooling。\n"
                "- priority_level 只能是 high, medium, low。\n"
                "- source_item_ids 只能引用候选信号中的来源条目 id。\n"
                f"\n候选信号：\n{json.dumps(cluster_payload, ensure_ascii=False)}"
            ),
        ),
    ]


def _materialize_output(
    *,
    draft: _DraftBrief,
    source_items: list[AiHotTrackerSourceItem],
    signal_clusters: list[AiHotTrackerSignalCluster],
) -> AiHotTrackerBriefOutput:
    item_map = {item.id: item for item in source_items}
    cluster_map = {cluster.cluster_id: cluster for cluster in signal_clusters}
    item_to_cluster = {item.id: item.cluster_id for item in source_items if item.cluster_id}

    signals = [
        AiHotTrackerBriefSignal(
            title=signal.title.strip(),
            summary=signal.summary.strip(),
            why_now=signal.why_now.strip(),
            impact=signal.impact.strip(),
            audience=_normalize_audience(signal.audience),
            change_type=_normalize_change_type(signal.change_type),
            priority_level=_normalize_priority_level(signal.priority_level),
            confidence=_normalize_confidence(signal.confidence),
            source_item_ids=_filter_item_ids(signal.source_item_ids, item_map),
        )
        for signal in draft.signals[:6]
        if signal.title.strip() and signal.summary.strip()
    ]

    if not signals:
        for cluster in signal_clusters[:3]:
            representative = item_map.get(cluster.representative_item_id)
            summary = representative.summary if representative else cluster.title
            signals.append(
                AiHotTrackerBriefSignal(
                    title=cluster.title,
                    summary=summary[:220],
                    why_now=_build_default_why_now(cluster),
                    impact=_build_default_impact(cluster, representative),
                    audience=_build_default_audience(representative),
                    change_type=_resolve_cluster_change_type(cluster),
                    priority_level=cluster.priority_level,
                    confidence=_build_default_confidence(cluster, representative),
                    source_item_ids=cluster.source_item_ids,
                )
            )

    keep_watching = [
        AiHotTrackerKeepWatchingItem(
            title=item.title.strip(),
            reason=item.reason.strip(),
            source_item_ids=_filter_item_ids(item.source_item_ids, item_map),
        )
        for item in draft.keep_watching[:4]
        if item.title.strip() and item.reason.strip()
    ]

    if not keep_watching:
        for cluster in signal_clusters[3:5]:
            keep_watching.append(
                AiHotTrackerKeepWatchingItem(
                    title=cluster.title,
                    reason="这个信号已经出现，但还需要继续观察后续版本、用户反馈或更多来源变化。",
                    source_item_ids=cluster.source_item_ids,
                )
            )

    blindspots = [
        entry.strip()
        for entry in draft.blindspots[:3]
        if isinstance(entry, str) and entry.strip()
    ]
    if not blindspots:
        blindspots = _build_default_blindspots(signal_clusters)

    reference_sources = _build_reference_sources(
        signals=signals,
        keep_watching=keep_watching,
        item_map=item_map,
        cluster_map=cluster_map,
        item_to_cluster=item_to_cluster,
    )

    return AiHotTrackerBriefOutput(
        headline=draft.headline.strip(),
        summary=draft.summary.strip(),
        change_state=_normalize_change_state(draft.change_state),
        signals=signals,
        keep_watching=keep_watching,
        blindspots=blindspots,
        reference_sources=reference_sources,
    )


def _build_reference_sources(
    *,
    signals: list[AiHotTrackerBriefSignal],
    keep_watching: list[AiHotTrackerKeepWatchingItem],
    item_map: dict[str, AiHotTrackerSourceItem],
    cluster_map: dict[str, AiHotTrackerSignalCluster],
    item_to_cluster: dict[str, str],
) -> list[AiHotTrackerReferenceSource]:
    references: list[AiHotTrackerReferenceSource] = []
    seen_urls: set[str] = set()
    ordered_item_ids: list[str] = []

    for signal in signals:
        ordered_item_ids.extend(signal.source_item_ids)
    for item in keep_watching:
        ordered_item_ids.extend(item.source_item_ids)

    for item_id in ordered_item_ids:
        item = item_map.get(item_id)
        if item is None or item.url in seen_urls:
            continue
        cluster = cluster_map.get(item_to_cluster.get(item_id, ""))
        seen_urls.add(item.url)
        references.append(
            AiHotTrackerReferenceSource(
                label=(cluster.title if cluster else item.title)[:96],
                url=item.url,
                source_kind=_resolve_reference_kind(item),
            )
        )
    return references


def _resolve_reference_kind(item: AiHotTrackerSourceItem) -> str:
    if item.source_family == "media":
        return "media"
    if item.source_family == "research" or "arxiv.org" in item.url:
        return "paper"
    if item.source_family == "open_source" or "github.com" in item.url:
        return "repository"
    if "docs" in item.url:
        return "docs"
    return "official"


def _normalize_priority_level(value: str) -> str:
    if value in {"high", "medium", "low"}:
        return value
    return "medium"


def _normalize_confidence(value: str) -> str:
    if value in {"high", "medium", "low"}:
        return value
    return "medium"


def _normalize_change_state(value: str) -> str:
    if value in {"first_run", "meaningful_update", "steady_state", "degraded", "failed"}:
        return value
    return "meaningful_update"


def _normalize_change_type(value: str) -> AiHotTrackerSignalChangeType:
    if value in {"new", "continuing", "cooling"}:
        return value
    return "continuing"


def _normalize_audience(value: list[str]) -> list[str]:
    cleaned = [item.strip() for item in value if item.strip()]
    return list(dict.fromkeys(cleaned))[:4] or ["AI 用户"]


def _filter_item_ids(
    item_ids: list[str],
    item_map: dict[str, AiHotTrackerSourceItem],
) -> list[str]:
    return [item_id for item_id in item_ids if item_id in item_map]


def _resolve_cluster_change_type(cluster: AiHotTrackerSignalCluster) -> AiHotTrackerSignalChangeType:
    if cluster.is_new:
        return "new"
    if cluster.is_cooling:
        return "cooling"
    return "continuing"


def _build_default_why_now(cluster: AiHotTrackerSignalCluster) -> str:
    if cluster.is_new:
        return "这是本轮新出现的信号，值得优先确认它会不会继续扩大影响。"
    if cluster.priority_level == "high":
        return "这条信号优先级较高，已经值得这一轮直接重点关注。"
    if cluster.is_continuing:
        return "这条信号还在延续，下一步要看它会不会继续强化或转向。"
    return "这条信号已经进入候选集合，值得继续观察后续变化。"


def _build_default_impact(
    cluster: AiHotTrackerSignalCluster,
    representative: AiHotTrackerSourceItem | None,
) -> str:
    if representative and "ordinary_user" in representative.audience_tags:
        return "它可能直接影响大众 AI 用户近期能用到的产品能力和使用选择。"
    if cluster.category in {"developer_tools", "open_source"}:
        return "它会影响开发者构建、部署或评估 AI 应用的方式。"
    if cluster.category == "business":
        return "它可能改变 AI 产品竞争、商业化节奏或行业判断。"
    return "它会改变用户理解 AI 能力边界和后续趋势的方式。"


def _build_default_audience(item: AiHotTrackerSourceItem | None) -> list[str]:
    if item is None:
        return ["AI 用户"]
    mapping = {
        "ordinary_user": "AI 用户",
        "developer": "开发者",
        "product_builder": "产品人",
        "learner": "学习者",
    }
    return [mapping.get(tag, tag) for tag in item.audience_tags[:4]] or ["AI 用户"]


def _build_default_confidence(
    cluster: AiHotTrackerSignalCluster,
    representative: AiHotTrackerSourceItem | None,
) -> str:
    source_count = len(cluster.source_item_ids)
    if source_count >= 3 or (
        representative is not None
        and representative.source_family == "official"
        and representative.rank_score >= 0.82
    ):
        return "high"
    if cluster.priority_level == "low":
        return "low"
    return "medium"


def _build_default_blindspots(signal_clusters: list[AiHotTrackerSignalCluster]) -> list[str]:
    if not signal_clusters:
        return ["这一轮缺少足够稳定的候选信号，仍需等待更完整来源。"]
    if any(cluster.priority_level == "high" and cluster.is_new for cluster in signal_clusters):
        return [
            "高优先级新信号已经出现，但还需要继续观察版本落地、用户反馈或更多官方跟进。",
            "媒体和社区讨论可能先行升温，后续要继续确认是否有真实产品影响。",
        ]
    return [
        "这一轮更多是延续性变化，仍需观察后续版本、落地场景或更多来源交叉确认。",
    ]


def _build_degraded_report(
    *,
    intake: AiHotTrackerSourceIntakeResult,
    tracking_profile: AiHotTrackerTrackingProfile,
    generated_at: datetime,
    decision_result: AiHotTrackerDecisionResult,
    degraded_reason: str,
    headline: str,
    summary: str,
    keep_watching_reason: str,
) -> AiHotTrackerReportResponse:
    question = build_ai_hot_tracker_internal_question(tracking_profile)
    keep_watching = [
        AiHotTrackerKeepWatchingItem(
            title=cluster.title,
            reason=keep_watching_reason,
            source_item_ids=cluster.source_item_ids,
        )
        for cluster in decision_result.candidate_clusters[:3]
    ]
    output = AiHotTrackerBriefOutput(
        headline=headline,
        summary=summary,
        change_state="degraded",
        signals=[],
        keep_watching=keep_watching,
        blindspots=_build_default_blindspots(decision_result.signal_clusters),
        reference_sources=[],
    )
    return AiHotTrackerReportResponse(
        title=headline,
        question=question,
        output=output,
        source_catalog=intake.source_catalog,
        source_items=decision_result.source_items,
        source_failures=intake.source_failures,
        source_set=_build_source_set(
            intake=intake,
            tracking_profile=tracking_profile,
            generated_at=generated_at,
            question=question,
            decision_result=decision_result,
        ),
        generated_at=generated_at,
        degraded_reason=degraded_reason,
    )


def _build_source_set(
    *,
    intake: AiHotTrackerSourceIntakeResult,
    tracking_profile: AiHotTrackerTrackingProfile,
    generated_at: datetime,
    question: str,
    decision_result: AiHotTrackerDecisionResult,
) -> dict[str, object]:
    return {
        "mode": "ai_hot_tracker_tracking_agent",
        "generated_at": generated_at.isoformat(),
        "tracking_profile": tracking_profile.model_dump(mode="json"),
        "tracking_profile_summary": {
            "topic": tracking_profile.topic,
            "scope": tracking_profile.scope,
            "source_strategy": tracking_profile.source_strategy,
            "enabled_categories": tracking_profile.enabled_categories,
        },
        "decision_summary": {
            "source_count": len(intake.source_catalog),
            "source_item_count": len(decision_result.source_items),
            "source_failure_count": len(intake.source_failures),
            "cluster_count": len(decision_result.signal_clusters),
            "candidate_cluster_count": len(decision_result.candidate_clusters),
            "event_memory_count": len(decision_result.signal_memories),
        },
        "question": question,
        "source_catalog": [item.model_dump(mode="json") for item in intake.source_catalog],
        "source_items": [item.model_dump(mode="json") for item in decision_result.source_items],
        "source_failures": [item.model_dump(mode="json") for item in intake.source_failures],
        "signal_clusters": [item.model_dump(mode="json") for item in decision_result.signal_clusters],
        "candidate_cluster_ids": [item.cluster_id for item in decision_result.candidate_clusters],
        "cluster_snapshot": [item.model_dump(mode="json") for item in decision_result.cluster_snapshot],
        "event_memories": [item.model_dump(mode="json") for item in decision_result.signal_memories],
        "agent_trace": [
            {
                "role": "scout",
                "summary": (
                    f"扫描 {len(intake.source_catalog)} 个来源，拿到 {len(decision_result.source_items)} 条标准化条目，"
                    f"失败 {len(intake.source_failures)} 个来源。"
                ),
                "status": "completed" if not intake.source_failures else "degraded",
                "details": {
                    "source_count": len(intake.source_catalog),
                    "item_count": len(decision_result.source_items),
                    "failure_count": len(intake.source_failures),
                },
            },
            {
                "role": "resolver",
                "summary": (
                    f"把 {len(decision_result.source_items)} 条来源条目收成 "
                    f"{len(decision_result.signal_clusters)} 个可读信号。"
                ),
                "status": "completed",
                "details": {
                    "cluster_count": len(decision_result.signal_clusters),
                    "candidate_cluster_count": len(decision_result.candidate_clusters),
                },
            },
            {
                "role": "analyst",
                "summary": (
                    f"本轮筛出 {len(decision_result.candidate_clusters)} 个进入简报候选的信号，"
                    f"并刷新 {len(decision_result.signal_memories)} 条事件记忆。"
                ),
                "status": "completed",
                "details": {
                    "candidate_cluster_ids": [item.cluster_id for item in decision_result.candidate_clusters],
                    "event_memory_count": len(decision_result.signal_memories),
                },
            },
        ],
    }


def _fallback_headline(output: AiHotTrackerBriefOutput, generated_at: datetime) -> str:
    if output.signals:
        return output.signals[0].title[:80]
    if output.keep_watching:
        return output.keep_watching[0].title[:80]
    return f"AI 热点追踪 {generated_at.strftime('%m/%d %H:%M')}"
