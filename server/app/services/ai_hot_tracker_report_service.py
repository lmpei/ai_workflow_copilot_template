import json
from datetime import UTC, datetime

from pydantic import BaseModel, Field, ValidationError

from app.repositories import workspace_repository
from app.schemas.ai_frontier_research import (
    AiFrontierEvent,
    AiFrontierProjectCard,
    AiFrontierReferenceSource,
    AiFrontierResearchOutput,
    AiFrontierTheme,
    AiHotTrackerReportResponse,
    AiHotTrackerSourceItem,
    AiHotTrackerTrackingProfile,
    normalize_ai_hot_tracker_tracking_profile,
)
from app.services.ai_hot_tracker_source_service import (
    AiHotTrackerSourceIntakeResult,
    fetch_ai_hot_tracker_source_items,
)
from app.services.model_interface_service import ModelInterfaceError, ModelMessage
from app.services.retrieval_generation_service import get_chat_model_interface

REPORT_SOURCE_ITEM_LIMIT = 10
REPORT_SOURCE_SUMMARY_LIMIT = 220


class AiHotTrackerReportGenerationError(Exception):
    pass


class AiHotTrackerReportAccessError(Exception):
    pass


class _DraftTheme(BaseModel):
    label: str
    summary: str


class _DraftEvent(BaseModel):
    title: str
    summary: str
    significance: str
    source_item_ids: list[str] = Field(default_factory=list)


class _DraftProjectCard(BaseModel):
    title: str
    summary: str
    why_it_matters: str
    source_item_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class _DraftReport(BaseModel):
    title: str
    frontier_summary: str
    trend_judgment: str
    themes: list[_DraftTheme] = Field(default_factory=list)
    events: list[_DraftEvent] = Field(default_factory=list)
    project_cards: list[_DraftProjectCard] = Field(default_factory=list)
    reference_item_ids: list[str] = Field(default_factory=list)


def build_ai_hot_tracker_internal_question(profile: AiHotTrackerTrackingProfile) -> str:
    return (
        f"请围绕「{profile.topic}」生成本轮 AI 热点追踪简报。"
        f"范围限定为：{profile.scope}"
    )


def filter_ai_hot_tracker_source_intake(
    *,
    intake: AiHotTrackerSourceIntakeResult,
    tracking_profile: AiHotTrackerTrackingProfile,
) -> AiHotTrackerSourceIntakeResult:
    allowed_categories = set(tracking_profile.enabled_categories)
    if not allowed_categories:
        return intake

    filtered_catalog = [
        source
        for source in intake.source_catalog
        if source.category in allowed_categories
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
            failure
            for failure in intake.source_failures
            if failure.source_id in allowed_source_ids
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
    generated_at: datetime | None = None,
) -> AiHotTrackerReportResponse:
    final_generated_at = generated_at or datetime.now(UTC)
    question = build_ai_hot_tracker_internal_question(tracking_profile)

    if not intake.source_items:
        return _build_degraded_report(
            intake=intake,
            tracking_profile=tracking_profile,
            generated_at=final_generated_at,
            degraded_reason="source_intake_unavailable",
            summary="本轮没有从可信来源拿到足够的有效条目，暂时无法形成可用简报。",
            judgment="先不要给出趋势判断，建议稍后重新获取来源。",
        )

    try:
        draft = _generate_report_draft(
            intake=intake,
            tracking_profile=tracking_profile,
            question=question,
        )
    except AiHotTrackerReportGenerationError:
        return _build_degraded_report(
            intake=intake,
            tracking_profile=tracking_profile,
            generated_at=final_generated_at,
            degraded_reason="report_generation_failed",
            summary="本轮已经更新了来源，但结构化简报没有成功生成。",
            judgment="来源已更新，判断层失败。本轮结果应视为不完整，建议稍后重新运行。",
        )

    output = _materialize_output(draft=draft, source_items=intake.source_items)
    degraded_reason = "source_intake_partial" if intake.source_failures else None
    return AiHotTrackerReportResponse(
        title=draft.title.strip() or _fallback_title(output, final_generated_at),
        question=question,
        output=output,
        source_catalog=intake.source_catalog,
        source_items=intake.source_items,
        source_failures=intake.source_failures,
        source_set=_build_source_set(
            intake=intake,
            tracking_profile=tracking_profile,
            generated_at=final_generated_at,
            question=question,
        ),
        generated_at=final_generated_at,
        degraded_reason=degraded_reason,
    )


def _generate_report_draft(
    *,
    intake: AiHotTrackerSourceIntakeResult,
    tracking_profile: AiHotTrackerTrackingProfile,
    question: str,
) -> _DraftReport:
    interface = get_chat_model_interface()
    selected_items = _select_report_source_items(intake.source_items)
    source_payload = _build_source_payload(selected_items)
    messages = _build_generation_messages(
        source_payload=source_payload,
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
                return _DraftReport.model_validate(response.data)
            except ValidationError as validation_error:
                return _repair_report_draft(
                    interface=interface,
                    source_payload=source_payload,
                    invalid_data=response.data,
                    validation_error=validation_error,
                    tracking_profile=tracking_profile,
                )
        except ModelInterfaceError as error:
            last_model_error = error

    raise AiHotTrackerReportGenerationError("Failed to generate AI hot tracker report draft") from last_model_error


def _repair_report_draft(
    *,
    interface,
    source_payload: list[dict[str, object]],
    invalid_data: dict[str, object],
    validation_error: ValidationError,
    tracking_profile: AiHotTrackerTrackingProfile,
) -> _DraftReport:
    messages = [
        ModelMessage(
            role="system",
            content=(
                "你是 JSON 修复器。"
                "你的任务不是重写报告，而是把已有 JSON 修成符合目标 schema 的 JSON object。"
                "不要输出 Markdown，不要输出代码块，只输出合法 JSON。"
            ),
        ),
        ModelMessage(
            role="user",
            content=(
                f"追踪主题：{tracking_profile.topic}\n"
                f"追踪范围：{tracking_profile.scope}\n"
                "请修复下面这份不合法的 JSON。\n"
                "必须保留字段：title, frontier_summary, trend_judgment, themes, events, "
                "project_cards, reference_item_ids。\n"
                "themes 最多 4 条，events 最多 5 条，project_cards 最多 6 条。\n"
                "events 和 project_cards 中的 source_item_ids 只能引用来源条目的 id。\n"
                "reference_item_ids 也只能引用来源条目的 id。\n"
                f"\n来源条目：\n{json.dumps(source_payload, ensure_ascii=False)}"
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
        return _DraftReport.model_validate(response.data)
    except (ModelInterfaceError, ValidationError) as error:
        raise AiHotTrackerReportGenerationError("Failed to repair AI hot tracker report draft") from error


def _build_source_payload(source_items: list[AiHotTrackerSourceItem]) -> list[dict[str, object]]:
    return [
        {
            "id": item.id,
            "source": item.source_label,
            "category": item.category,
            "title": item.title,
            "summary": item.summary[:REPORT_SOURCE_SUMMARY_LIMIT],
            "url": item.url,
            "published_at": item.published_at.isoformat() if item.published_at else None,
            "tags": item.tags,
        }
        for item in source_items
    ]


def _select_report_source_items(source_items: list[AiHotTrackerSourceItem]) -> list[AiHotTrackerSourceItem]:
    if len(source_items) <= REPORT_SOURCE_ITEM_LIMIT:
        return source_items

    selected: list[AiHotTrackerSourceItem] = []
    category_counts: dict[str, int] = {}
    seen_ids: set[str] = set()

    for item in source_items:
        if category_counts.get(item.category, 0) >= 2:
            continue
        selected.append(item)
        seen_ids.add(item.id)
        category_counts[item.category] = category_counts.get(item.category, 0) + 1
        if len(selected) >= REPORT_SOURCE_ITEM_LIMIT:
            return selected

    for item in source_items:
        if item.id in seen_ids:
            continue
        selected.append(item)
        if len(selected) >= REPORT_SOURCE_ITEM_LIMIT:
            break

    return selected


def _build_generation_messages(
    *,
    source_payload: list[dict[str, object]],
    tracking_profile: AiHotTrackerTrackingProfile,
    question: str,
) -> list[ModelMessage]:
    return [
        ModelMessage(
            role="system",
            content=(
                "你是 AI 热点追踪模块的结构化简报生成器。"
                "你只能基于提供的可信来源条目生成结果，不能引入未提供的外部事实。"
                "输出要像面向用户的追踪简报，而不是系统说明。"
                "如果证据不足，就收窄结论，不要强行延展。"
                "只输出一个合法 JSON object。"
            ),
        ),
        ModelMessage(
            role="user",
            content=(
                f"追踪主题：{tracking_profile.topic}\n"
                f"追踪范围：{tracking_profile.scope}\n"
                f"本轮任务：{question}\n\n"
                "请基于下面的来源条目生成结构化简报。\n"
                "必须输出字段：title, frontier_summary, trend_judgment, themes, events, "
                "project_cards, reference_item_ids。\n"
                "- title：像简报标题，不要写成问题。\n"
                "- frontier_summary：一段直接结论，适合放在报告最前面。\n"
                "- trend_judgment：说明这轮最重要的判断，以及后续应该继续盯什么。\n"
                "- themes：每项包含 label 和 summary。\n"
                "- events：每项包含 title, summary, significance, source_item_ids。\n"
                "- project_cards：每项包含 title, summary, why_it_matters, source_item_ids, tags。\n"
                "- reference_item_ids：只允许引用来源条目的 id。\n"
                "数量限制：themes 最多 4 条，events 最多 5 条，project_cards 最多 6 条。\n"
                f"\n来源条目：\n{json.dumps(source_payload, ensure_ascii=False)}"
            ),
        ),
    ]


def _materialize_output(
    *,
    draft: _DraftReport,
    source_items: list[AiHotTrackerSourceItem],
) -> AiFrontierResearchOutput:
    item_map = {item.id: item for item in source_items}

    project_cards: list[AiFrontierProjectCard] = []
    for card in draft.project_cards:
        supporting_item = _pick_first_item(card.source_item_ids, item_map)
        project_cards.append(
            AiFrontierProjectCard(
                title=card.title,
                source_label=supporting_item.source_label if supporting_item else "可信来源",
                summary=card.summary,
                why_it_matters=card.why_it_matters,
                official_url=supporting_item.url if supporting_item else None,
                repo_url=supporting_item.url if supporting_item and "github.com" in supporting_item.url else None,
                docs_url=supporting_item.url if supporting_item and "docs" in supporting_item.url else None,
                tags=card.tags or (supporting_item.tags if supporting_item else []),
                source_item_ids=card.source_item_ids,
            )
        )

    references = _build_reference_sources(
        reference_item_ids=draft.reference_item_ids,
        project_cards=draft.project_cards,
        item_map=item_map,
    )

    return AiFrontierResearchOutput(
        frontier_summary=draft.frontier_summary.strip(),
        trend_judgment=draft.trend_judgment.strip(),
        themes=[AiFrontierTheme(label=item.label, summary=item.summary) for item in draft.themes],
        events=[
            AiFrontierEvent(
                title=item.title,
                summary=item.summary,
                significance=item.significance,
                source_item_ids=item.source_item_ids,
            )
            for item in draft.events
        ],
        project_cards=project_cards,
        reference_sources=references,
    )


def _build_reference_sources(
    *,
    reference_item_ids: list[str],
    project_cards: list[_DraftProjectCard],
    item_map: dict[str, AiHotTrackerSourceItem],
) -> list[AiFrontierReferenceSource]:
    references: list[AiFrontierReferenceSource] = []
    seen_urls: set[str] = set()
    ordered_ids = list(reference_item_ids)
    for card in project_cards:
        ordered_ids.extend(card.source_item_ids)

    for item_id in ordered_ids:
        item = item_map.get(item_id)
        if item is None or item.url in seen_urls:
            continue
        seen_urls.add(item.url)
        references.append(
            AiFrontierReferenceSource(
                label=f"{item.source_label} · {item.title}",
                url=item.url,
                source_kind=_resolve_reference_kind(item.url),
            )
        )
    return references


def _resolve_reference_kind(url: str) -> str:
    if "arxiv.org" in url:
        return "paper"
    if "github.com" in url:
        return "repository"
    if "docs" in url:
        return "docs"
    return "official"


def _pick_first_item(
    item_ids: list[str],
    item_map: dict[str, AiHotTrackerSourceItem],
) -> AiHotTrackerSourceItem | None:
    for item_id in item_ids:
        item = item_map.get(item_id)
        if item is not None:
            return item
    return None


def _build_degraded_report(
    *,
    intake: AiHotTrackerSourceIntakeResult,
    tracking_profile: AiHotTrackerTrackingProfile,
    generated_at: datetime,
    degraded_reason: str,
    summary: str,
    judgment: str,
) -> AiHotTrackerReportResponse:
    question = build_ai_hot_tracker_internal_question(tracking_profile)
    output = AiFrontierResearchOutput(
        frontier_summary=summary,
        trend_judgment=judgment,
        themes=[AiFrontierTheme(label="本轮状态", summary=judgment)],
        events=[],
        project_cards=[],
        reference_sources=[],
    )
    return AiHotTrackerReportResponse(
        title="本轮暂无有效热点",
        question=question,
        output=output,
        source_catalog=intake.source_catalog,
        source_items=intake.source_items,
        source_failures=intake.source_failures,
        source_set=_build_source_set(
            intake=intake,
            tracking_profile=tracking_profile,
            generated_at=generated_at,
            question=question,
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
) -> dict[str, object]:
    return {
        "mode": "ai_hot_tracker_tracking_agent",
        "generated_at": generated_at.isoformat(),
        "tracking_profile": tracking_profile.model_dump(mode="json"),
        "question": question,
        "source_catalog": [item.model_dump(mode="json") for item in intake.source_catalog],
        "source_items": [item.model_dump(mode="json") for item in intake.source_items],
        "source_failures": [item.model_dump(mode="json") for item in intake.source_failures],
    }


def _fallback_title(output: AiFrontierResearchOutput, generated_at: datetime) -> str:
    if output.events:
        return output.events[0].title[:80]
    if output.project_cards:
        return output.project_cards[0].title[:80]
    if output.themes:
        return f"{output.themes[0].label} 追踪"[:80]
    return f"AI 热点追踪 {generated_at.strftime('%m/%d %H:%M')}"
