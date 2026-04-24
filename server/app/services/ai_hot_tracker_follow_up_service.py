from __future__ import annotations

from datetime import UTC, datetime

from app.schemas.ai_frontier_research import (
    AiFrontierFollowUpEntry,
    AiHotTrackerSignalMemoryRecord,
    AiHotTrackerTrackingRunFollowUpRequest,
    AiHotTrackerTrackingRunFollowUpResponse,
    AiHotTrackerTrackingRunResponse,
)
from app.services.model_interface_service import ModelInterfaceError, ModelMessage
from app.services.retrieval_generation_service import ChatProcessingError, get_chat_model_interface


def _render_signal_section(run: AiHotTrackerTrackingRunResponse) -> str:
    if not run.output.signals:
        return "- 本轮还没有形成可解释的主信号。"

    sections: list[str] = []
    for signal in run.output.signals:
        sections.append(
            "\n".join(
                [
                    f"- {signal.title}",
                    f"  简述：{signal.summary}",
                    f"  为什么现在值得看：{signal.why_now}",
                    f"  影响：{signal.impact or '当前还缺少更具体的影响判断。'}",
                    f"  适合谁关注：{'、'.join(signal.audience) or 'AI 用户'}",
                    f"  判断把握：{signal.confidence}",
                ]
            )
        )
    return "\n".join(sections)


def _render_keep_watching_section(run: AiHotTrackerTrackingRunResponse) -> str:
    if not run.output.keep_watching:
        return "- 当前没有额外的继续观察项。"
    return "\n".join(f"- {item.title}：{item.reason}" for item in run.output.keep_watching)


def _render_blindspots(run: AiHotTrackerTrackingRunResponse) -> str:
    if not run.output.blindspots:
        return "- 当前没有额外的盲区说明。"
    return "\n".join(f"- {item}" for item in run.output.blindspots)


def _render_references(run: AiHotTrackerTrackingRunResponse) -> str:
    if not run.output.reference_sources:
        return "- 当前没有显式参考来源。"
    return "\n".join(f"- {source.label}: {source.url}" for source in run.output.reference_sources)


def _render_source_items(run: AiHotTrackerTrackingRunResponse) -> str:
    if not run.source_items:
        return "- 当前没有可用来源条目。"
    return "\n".join(
        f"- {item.title}: {item.summary} ({item.source_label}, {item.url})"
        for item in run.source_items
    )


def _render_follow_ups(run: AiHotTrackerTrackingRunResponse) -> str:
    if not run.follow_ups:
        return "- 当前还没有历史追问。"
    return "\n".join(f"- 问：{item.question}\n  答：{item.answer}" for item in run.follow_ups)


def _load_event_memories(run: AiHotTrackerTrackingRunResponse) -> list[AiHotTrackerSignalMemoryRecord]:
    if not isinstance(run.source_set, dict):
        return []

    raw_memories = run.source_set.get("event_memories")
    if not isinstance(raw_memories, list):
        return []

    return [
        AiHotTrackerSignalMemoryRecord.model_validate(item)
        for item in raw_memories
        if isinstance(item, dict)
    ]


def _render_event_memories(run: AiHotTrackerTrackingRunResponse) -> str:
    memories = _load_event_memories(run)
    if not memories:
        return "- 当前没有额外事件记忆。"

    sections: list[str] = []
    for memory in memories[:6]:
        sections.append(
            "\n".join(
                [
                    f"- {memory.title}",
                    f"  连续状态：{memory.continuity_state}",
                    f"  活跃状态：{memory.activity_state}",
                    f"  最近优先级：{memory.latest_priority_level}",
                    f"  连续轮次：{memory.streak_count}",
                    f"  备注：{memory.note or '无'}",
                ]
            )
        )
    return "\n".join(sections)


def _render_run_context(run: AiHotTrackerTrackingRunResponse) -> str:
    return "\n\n".join(
        [
            f"简报标题：{run.title}",
            f"本轮任务：{run.question}",
            f"本轮摘要：{run.output.summary}",
            f"变化状态：{run.output.change_state}",
            f"运行结论：{run.delta.summary}",
            f"通知理由：{run.delta.notify_reason or '本轮没有触发额外通知'}",
            f"主信号：\n{_render_signal_section(run)}",
            f"继续观察：\n{_render_keep_watching_section(run)}",
            f"当前盲区：\n{_render_blindspots(run)}",
            f"事件记忆：\n{_render_event_memories(run)}",
            f"参考来源：\n{_render_references(run)}",
            f"来源条目：\n{_render_source_items(run)}",
            f"已有追问：\n{_render_follow_ups(run)}",
        ]
    )


def _build_low_evidence_answer(run: AiHotTrackerTrackingRunResponse) -> str:
    blindspot_text = "；".join(run.output.blindspots[:2]) if run.output.blindspots else "当前这一轮还没有足够来源支撑进一步判断"
    return (
        "这轮简报的证据还不够完整，我只能基于当前 run 给出保守回答。"
        f" 目前最需要补看的地方是：{blindspot_text}。"
    )


def _normalize_text(value: str | None) -> str:
    return (value or "").strip().casefold()


def _resolve_follow_up_grounding(
    *,
    run: AiHotTrackerTrackingRunResponse,
    payload: AiHotTrackerTrackingRunFollowUpRequest,
) -> tuple[list[str], list[str], list[str], list[str]]:
    normalized_focus_label = _normalize_text(payload.focus_label)
    normalized_focus_context = _normalize_text(payload.focus_context)

    focused_source_ids: list[str] = []
    grounding_notes: list[str] = []

    for signal in run.output.signals:
        signal_title = _normalize_text(signal.title)
        signal_summary = _normalize_text(signal.summary)
        if normalized_focus_label and normalized_focus_label in signal_title:
            focused_source_ids.extend(signal.source_item_ids)
            grounding_notes.append("围绕用户当前选中的主信号回答。")
            break
        if normalized_focus_context and (
            signal_title in normalized_focus_context or signal_summary in normalized_focus_context
        ):
            focused_source_ids.extend(signal.source_item_ids)
            grounding_notes.append("围绕用户当前聚焦的主信号内容回答。")
            break

    if not focused_source_ids:
        for item in run.output.keep_watching:
            item_title = _normalize_text(item.title)
            item_reason = _normalize_text(item.reason)
            if normalized_focus_label and normalized_focus_label in item_title:
                focused_source_ids.extend(item.source_item_ids)
                grounding_notes.append("围绕继续观察项回答。")
                break
            if normalized_focus_context and (
                item_title in normalized_focus_context or item_reason in normalized_focus_context
            ):
                focused_source_ids.extend(item.source_item_ids)
                grounding_notes.append("围绕用户当前聚焦的继续观察项回答。")
                break

    if not focused_source_ids:
        focused_source_ids.extend(
            item_id
            for signal in run.output.signals[:3]
            for item_id in signal.source_item_ids
        )
        if focused_source_ids:
            grounding_notes.append("默认围绕当前简报的主信号回答。")

    if not focused_source_ids:
        focused_source_ids.extend(item.id for item in run.source_items[:6])
        if focused_source_ids:
            grounding_notes.append("当前没有更窄的焦点，因此退回到本轮来源条目。")

    deduped_source_ids: list[str] = []
    seen_source_ids: set[str] = set()
    for item_id in focused_source_ids:
        if item_id in seen_source_ids:
            continue
        seen_source_ids.add(item_id)
        deduped_source_ids.append(item_id)

    source_item_by_id = {item.id: item for item in run.source_items}
    grounding_event_ids: list[str] = []
    for item_id in deduped_source_ids:
        event_id = source_item_by_id.get(item_id).event_id if source_item_by_id.get(item_id) is not None else None
        if event_id and event_id not in grounding_event_ids:
            grounding_event_ids.append(event_id)

    grounding_blindspots = list(run.output.blindspots[:2]) if run.output.blindspots else []
    if grounding_blindspots:
        grounding_notes.append("回答同时受到本轮盲区约束。")

    if run.follow_ups:
        grounding_notes.append("回答延续当前 run 已有追问上下文。")

    return deduped_source_ids, grounding_event_ids, grounding_blindspots, grounding_notes


def answer_ai_hot_tracker_tracking_run_follow_up(
    *,
    run: AiHotTrackerTrackingRunResponse,
    payload: AiHotTrackerTrackingRunFollowUpRequest,
) -> AiHotTrackerTrackingRunFollowUpResponse:
    grounding_source_item_ids, grounding_event_ids, grounding_blindspots, grounding_notes = (
        _resolve_follow_up_grounding(run=run, payload=payload)
    )

    if not run.output.signals and not run.source_items:
        answer = _build_low_evidence_answer(run)
        return AiHotTrackerTrackingRunFollowUpResponse(
            answer=answer,
            follow_up=AiFrontierFollowUpEntry(
                question=payload.question,
                answer=answer,
                created_at=datetime.now(UTC),
                grounding_source_item_ids=grounding_source_item_ids,
                grounding_event_ids=grounding_event_ids,
                grounding_blindspots=grounding_blindspots,
                grounding_notes=grounding_notes or ["当前证据不足，因此只能给出保守回答。"],
            ),
        )

    focus_section = ""
    if payload.focus_label or payload.focus_context:
        focus_section = (
            f"\n\n用户当前聚焦：{payload.focus_label or '当前选中内容'}\n"
            f"{payload.focus_context or ''}"
        )

    prompt = (
        "你正在回答 AI 热点追踪模块里，围绕当前简报的一次追问。"
        " 你只能基于当前这份简报、来源条目、事件记忆、盲区说明和已有追问来回答。"
        " 不要扩展成新的泛研究，也不要引入上下文没有给出的外部事实。"
        " 如果问题超出了本轮依据，就明确说明当前还不能下结论，并指出还缺什么来源或信号。"
        " 回答面向大众 AI 用户，要清楚、具体、克制。"
        " 如果引用来源，请在句末用【来源：标题】标注。"
        f"\n\n当前 run 上下文：\n{_render_run_context(run)}"
        f"{focus_section}"
        f"\n\n当前回答必须优先依赖这些来源条目 ID：{', '.join(grounding_source_item_ids) or '无'}"
        f"\n当前回答必须优先依赖这些事件记忆 ID：{', '.join(grounding_event_ids) or '无'}"
        f"\n当前盲区：{'；'.join(grounding_blindspots) or '无'}"
        f"\n\n用户追问：{payload.question}"
    )

    try:
        response = get_chat_model_interface().generate_text(
            temperature=0.2,
            messages=[
                ModelMessage(
                    role="system",
                    content=(
                        "你是 AI 热点追踪模块里的简报解读助手。"
                        " 你的职责是解释当前简报与其来源，而不是扩展到脱离当前 run 的泛聊天。"
                        " 当依据不足时，要收窄回答并指出盲区。"
                    ),
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
            grounding_source_item_ids=grounding_source_item_ids,
            grounding_event_ids=grounding_event_ids,
            grounding_blindspots=grounding_blindspots,
            grounding_notes=grounding_notes,
        ),
    )
