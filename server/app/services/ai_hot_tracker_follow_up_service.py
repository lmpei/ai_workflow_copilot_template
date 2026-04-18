from datetime import UTC, datetime

from app.schemas.ai_frontier_research import (
    AiFrontierFollowUpEntry,
    AiHotTrackerFollowUpRequest,
    AiHotTrackerFollowUpResponse,
)
from app.services.model_interface_service import ModelInterfaceError, ModelMessage
from app.services.retrieval_generation_service import ChatProcessingError, get_chat_model_interface


def _render_output_context(payload: AiHotTrackerFollowUpRequest) -> str:
    output = payload.report_output
    themes = "\n".join(f"- {theme.label}: {theme.summary}" for theme in output.themes) or "- 暂无"
    events = (
        "\n".join(f"- {event.title}: {event.summary}（{event.significance}）" for event in output.events)
        or "- 暂无"
    )
    projects = (
        "\n".join(
            f"- {card.title}: {card.summary}（{card.why_it_matters}）" for card in output.project_cards
        )
        or "- 暂无"
    )
    references = "\n".join(f"- {source.label}: {source.url}" for source in output.reference_sources) or "- 暂无"

    source_items = payload.source_set.get("source_items") if isinstance(payload.source_set, dict) else None
    rendered_source_items = (
        "\n".join(
            f"- {item.get('title')}: {item.get('summary')} ({item.get('url')})"
            for item in source_items
            if isinstance(item, dict)
            and isinstance(item.get("title"), str)
            and isinstance(item.get("summary"), str)
            and isinstance(item.get("url"), str)
        )
        or "- 暂无"
    )

    prior_follow_ups = (
        "\n".join(f"- 问：{item.question}\n  答：{item.answer}" for item in payload.prior_follow_ups) or "- 暂无"
    )

    parts = [
        f"报告原始问题：{payload.report_question}",
        f"报告正文：\n{payload.report_answer or '无完整正文，仅保留结构化结果。'}",
        f"本轮摘要：\n{output.frontier_summary}",
        f"本轮判断：\n{output.trend_judgment}",
        f"主题：\n{themes}",
        f"事件：\n{events}",
        f"项目与框架：\n{projects}",
        f"参考来源：\n{references}",
        f"来源条目：\n{rendered_source_items}",
        f"已有追问：\n{prior_follow_ups}",
    ]
    return "\n\n".join(parts)


def answer_ai_hot_tracker_follow_up(payload: AiHotTrackerFollowUpRequest) -> AiHotTrackerFollowUpResponse:
    prompt = (
        "你正在回答一份 AI 热点追踪报告的追问。"
        "你只能根据当前这份报告和它已经引用的来源来解释，不能扩展成新的泛研究。"
        "回答要简洁、清楚、面向用户。如果报告里的证据还不够，就直接说明还缺什么。"
        f"\n\n当前报告上下文：\n{_render_output_context(payload)}"
        f"\n\n用户追问：{payload.follow_up_question}"
    )

    try:
        response = get_chat_model_interface().generate_text(
            temperature=0.2,
            messages=[
                ModelMessage(
                    role="system",
                    content="你是 AI 热点追踪模块里的报告解读助手，只解释当前报告，不扩写无关内容。",
                ),
                ModelMessage(role="user", content=prompt),
            ],
        )
    except ModelInterfaceError as error:
        raise ChatProcessingError("Failed to answer AI hot tracker follow-up") from error

    answer = response.text.strip()
    if not answer:
        raise ChatProcessingError("AI hot tracker follow-up returned an empty answer")

    return AiHotTrackerFollowUpResponse(
        answer=answer,
        follow_up=AiFrontierFollowUpEntry(
            question=payload.follow_up_question,
            answer=answer,
            created_at=datetime.now(UTC),
        ),
    )
