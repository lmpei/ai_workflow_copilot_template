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
)
from app.services.ai_hot_tracker_source_service import (
    AiHotTrackerSourceIntakeResult,
    fetch_ai_hot_tracker_source_items,
)
from app.services.model_interface_service import ModelInterfaceError, ModelMessage
from app.services.retrieval_generation_service import get_chat_model_interface

AI_HOT_TRACKER_INTERNAL_QUESTION = (
    "请根据本轮可信来源，提炼 AI 领域最近最值得关注的模型、产品、开源项目与工程生态变化，"
    "输出一份可读、可追溯、可保存的热点报告。"
)

REPORT_SOURCE_ITEM_LIMIT = 10
REPORT_SOURCE_SUMMARY_LIMIT = 180


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


def generate_ai_hot_tracker_report(*, workspace_id: str, user_id: str) -> AiHotTrackerReportResponse:
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise AiHotTrackerReportAccessError("Workspace not found")
    if workspace.module_type != "research":
        raise AiHotTrackerReportAccessError("AI hot tracker is only available in research workspaces")

    generated_at = datetime.now(UTC)
    intake = fetch_ai_hot_tracker_source_items()

    if not intake.source_items:
        return _build_degraded_report(
            intake=intake,
            generated_at=generated_at,
            degraded_reason="source_intake_unavailable",
            summary="本轮没有从可信来源拿到足够内容，因此暂时无法生成有效报告。",
            judgment="可信来源当前不可用，建议稍后重新获取。",
        )

    try:
        draft = _generate_report_draft(intake=intake)
    except AiHotTrackerReportGenerationError:
        return _build_degraded_report(
            intake=intake,
            generated_at=generated_at,
            degraded_reason="report_generation_failed",
            summary="本轮已经获取到外部来源，但结构化报告还没有成功生成。",
            judgment="来源已经更新，但判断生成失败，建议稍后重新获取。",
        )

    output = _materialize_output(draft=draft, source_items=intake.source_items)
    degraded_reason = "source_intake_partial" if intake.source_failures else None
    source_set = _build_source_set(intake=intake, generated_at=generated_at)
    return AiHotTrackerReportResponse(
        title=draft.title.strip() or _fallback_title(output, generated_at),
        question=AI_HOT_TRACKER_INTERNAL_QUESTION,
        output=output,
        source_catalog=intake.source_catalog,
        source_items=intake.source_items,
        source_failures=intake.source_failures,
        source_set=source_set,
        generated_at=generated_at,
        degraded_reason=degraded_reason,
    )


def _generate_report_draft(*, intake: AiHotTrackerSourceIntakeResult) -> _DraftReport:
    interface = get_chat_model_interface()
    selected_items = _select_report_source_items(intake.source_items)
    source_payload = _build_source_payload(selected_items)
    messages = _build_generation_messages(source_payload)

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
) -> _DraftReport:
    messages = [
        ModelMessage(
            role="system",
            content=(
                "你是结构化 JSON 修正器。"
                "你的任务不是重新写一篇报告，而是把已有 JSON 修成符合目标 schema 的 JSON object。"
                "不得输出 Markdown，不得输出代码块，只能输出一个合法 JSON object。"
            ),
        ),
        ModelMessage(
            role="user",
            content=(
                "下面是来源条目、上一次生成出的 JSON，以及校验失败信息。\n"
                "请在保留原意的前提下修正 JSON，使其符合这些字段："
                "title, frontier_summary, trend_judgment, themes, events, project_cards, reference_item_ids。\n"
                "themes 最多 4 条，events 最多 5 条，project_cards 最多 6 条。\n"
                "events 与 project_cards 中的 source_item_ids 只能引用来源条目的 id。\n"
                "reference_item_ids 也只能引用来源条目的 id。\n"
                f"\n来源条目：\n{json.dumps(source_payload, ensure_ascii=False)}"
                f"\n\n上一次 JSON：\n{json.dumps(invalid_data, ensure_ascii=False)}"
                f"\n\n校验失败：\n{validation_error.json()}"
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


def _build_generation_messages(source_payload: list[dict[str, object]]) -> list[ModelMessage]:
    return [
        ModelMessage(
            role="system",
            content=(
                "你是 AI 热点追踪模块的结构化报告生成器。"
                "你只能基于提供的可信来源条目输出一份结构化热点报告。"
                "不要输出解释你做法的内部语言，不要引入未提供的外部事实。"
                "如果证据不足，要诚实收窄结论。"
                "只输出一个合法 JSON object，不要输出 Markdown 或代码块。"
            ),
        ),
        ModelMessage(
            role="user",
            content=(
                "请基于以下来源条目生成中文 JSON 报告。\n"
                "必须输出这些字段：title, frontier_summary, trend_judgment, themes, events, project_cards, reference_item_ids。\n"
                "字段要求：\n"
                "- title: 简洁、像报告标题\n"
                "- frontier_summary: 面向用户的直接摘要\n"
                "- trend_judgment: 本轮最重要的判断，不要写系统解释\n"
                "- themes: 每项都要包含 label 和 summary\n"
                "- events: 每项都要包含 title、summary、significance、source_item_ids\n"
                "- project_cards: 每项都要包含 title、summary、why_it_matters、source_item_ids、tags\n"
                "- reference_item_ids: 只允许引用来源条目的 id\n"
                "数量限制：themes 最多 4 条，events 最多 5 条，project_cards 最多 6 条。\n"
                "events 和 project_cards 里的 source_item_ids 只能引用提供条目的 id。\n"
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
    generated_at: datetime,
    degraded_reason: str,
    summary: str,
    judgment: str,
) -> AiHotTrackerReportResponse:
    output = AiFrontierResearchOutput(
        frontier_summary=summary,
        trend_judgment=judgment,
        themes=[AiFrontierTheme(label="本轮状态", summary=judgment)],
        events=[],
        project_cards=[],
        reference_sources=[],
    )
    return AiHotTrackerReportResponse(
        title="本轮热点暂不可用",
        question=AI_HOT_TRACKER_INTERNAL_QUESTION,
        output=output,
        source_catalog=intake.source_catalog,
        source_items=intake.source_items,
        source_failures=intake.source_failures,
        source_set=_build_source_set(intake=intake, generated_at=generated_at),
        generated_at=generated_at,
        degraded_reason=degraded_reason,
    )


def _build_source_set(
    *,
    intake: AiHotTrackerSourceIntakeResult,
    generated_at: datetime,
) -> dict[str, object]:
    return {
        "mode": "ai_hot_tracker_structured_report",
        "generated_at": generated_at.isoformat(),
        "source_catalog": [item.model_dump(mode="json") for item in intake.source_catalog],
        "source_items": [item.model_dump(mode="json") for item in intake.source_items],
        "source_failures": [item.model_dump(mode="json") for item in intake.source_failures],
        "question": AI_HOT_TRACKER_INTERNAL_QUESTION,
    }


def _fallback_title(output: AiFrontierResearchOutput, generated_at: datetime) -> str:
    if output.events:
        return output.events[0].title[:80]
    if output.project_cards:
        return output.project_cards[0].title[:80]
    if output.themes:
        return f"{output.themes[0].label} 追踪"[:80]
    return f"AI 热点追踪 {generated_at.strftime('%m/%d %H:%M')}"
