from datetime import UTC, datetime

from app.schemas.ai_frontier_research import (
    AiFrontierFollowUpEntry,
    AiHotTrackerTrackingRunFollowUpRequest,
    AiHotTrackerTrackingRunFollowUpResponse,
    AiHotTrackerTrackingRunResponse,
)
from app.services.model_interface_service import ModelInterfaceError, ModelMessage
from app.services.retrieval_generation_service import ChatProcessingError, get_chat_model_interface


def _render_run_context(run: AiHotTrackerTrackingRunResponse) -> str:
    output = run.output
    themes = "\n".join(f"- {theme.label}: {theme.summary}" for theme in output.themes) or "- 无"
    events = (
        "\n".join(
            f"- {event.title}: {event.summary}；为什么重要：{event.significance}"
            for event in output.events
        )
        or "- 无"
    )
    projects = (
        "\n".join(
            f"- {card.title}: {card.summary}；为什么值得继续看：{card.why_it_matters}"
            for card in output.project_cards
        )
        or "- 无"
    )
    references = (
        "\n".join(f"- {source.label}: {source.url}" for source in output.reference_sources) or "- 无"
    )
    source_items = (
        "\n".join(
            f"- {item.title}: {item.summary} ({item.url})"
            for item in run.source_items
        )
        or "- 无"
    )
    prior_follow_ups = (
        "\n".join(f"- 问：{item.question}\n  答：{item.answer}" for item in run.follow_ups) or "- 无"
    )

    return "\n\n".join(
        [
            f"报告标题：{run.title}",
            f"报告问题：{run.question}",
            f"本轮结论：{output.frontier_summary}",
            f"本轮判断：{output.trend_judgment}",
            f"变化总结：{run.delta.summary}",
            f"主题：\n{themes}",
            f"正在发生：\n{events}",
            f"值得继续看：\n{projects}",
            f"参考来源：\n{references}",
            f"来源条目：\n{source_items}",
            f"已存在追问：\n{prior_follow_ups}",
        ]
    )


def answer_ai_hot_tracker_tracking_run_follow_up(
    *,
    run: AiHotTrackerTrackingRunResponse,
    payload: AiHotTrackerTrackingRunFollowUpRequest,
) -> AiHotTrackerTrackingRunFollowUpResponse:
    focus_section = ""
    if payload.focus_label or payload.focus_context:
        focus_section = (
            f"\n\n用户当前焦点：{payload.focus_label or '当前选中内容'}\n"
            f"{payload.focus_context or ''}"
        )

    prompt = (
        "你正在回答 AI 热点追踪工作区里的一次追问。"
        "你只能根据当前这份报告及其来源解释，不得扩展成新的泛研究。"
        "回答要面向用户、简洁直接、可执行。"
        "如果证据不足，要明确说清楚缺什么。"
        "如果引用来源，请在句末用【来源：标题】标出。"
        f"\n\n当前运行上下文：\n{_render_run_context(run)}"
        f"{focus_section}"
        f"\n\n用户追问：{payload.question}"
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

    return AiHotTrackerTrackingRunFollowUpResponse(
        answer=answer,
        follow_up=AiFrontierFollowUpEntry(
            question=payload.question,
            answer=answer,
            created_at=datetime.now(UTC),
        ),
    )
