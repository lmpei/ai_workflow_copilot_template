from app.repositories import ai_frontier_research_record_repository, workspace_repository
from app.schemas.ai_frontier_research import (
    AiFrontierFollowUpEntry,
    AiFrontierResearchOutput,
    AiFrontierResearchRecordResponse,
    AiFrontierResearchRecordWriteRequest,
)


class AiFrontierResearchRecordAccessError(Exception):
    pass


def _build_record_title(title: str | None, question: str) -> str:
    title = (title or "").strip() or question.strip() or "AI frontier research record"
    return title[:255]


def create_ai_frontier_research_record(
    *,
    workspace_id: str,
    user_id: str,
    title: str | None,
    conversation_id: str | None,
    source_run_id: str | None,
    source_trace_id: str | None,
    question: str,
    answer_text: str | None,
    output: AiFrontierResearchOutput,
    follow_ups: list[AiFrontierFollowUpEntry],
    source_set: dict[str, object],
) -> AiFrontierResearchRecordResponse:
    persisted_source_set = dict(source_set)
    if answer_text:
        persisted_source_set["answer_text"] = answer_text
    persisted_source_set["follow_ups"] = [
        follow_up.model_dump(mode="json") for follow_up in follow_ups
    ]
    record = ai_frontier_research_record_repository.create_ai_frontier_research_record(
        workspace_id=workspace_id,
        conversation_id=conversation_id,
        source_run_id=source_run_id,
        source_trace_id=source_trace_id,
        created_by=user_id,
        title=_build_record_title(title, question),
        question=question,
        frontier_summary=output.frontier_summary,
        trend_judgment=output.trend_judgment,
        themes_json=[theme.model_dump() for theme in output.themes],
        events_json=[event.model_dump() for event in output.events],
        project_cards_json=[card.model_dump() for card in output.project_cards],
        reference_sources_json=[reference.model_dump() for reference in output.reference_sources],
        source_set_json=persisted_source_set,
    )
    return AiFrontierResearchRecordResponse.from_model(record)


def build_ai_frontier_source_set(
    *,
    mode: str,
    analysis_focus: str | None,
    search_query: str | None,
    connector_id: str | None,
    connector_consent_state: str | None,
    external_context_used: bool | None,
    external_match_count: int | None,
    selected_external_resource_snapshot_id: str | None,
    external_resource_snapshot_id: str | None,
    mcp_server_id: str | None,
    mcp_resource_id: str | None,
    mcp_tool_name: str | None,
    mcp_prompt_name: str | None,
    mcp_transport: str | None,
    mcp_read_status: str | None,
    context_selection_mode: str | None,
    source_titles: list[str],
) -> dict[str, object]:
    return {
        "mode": mode,
        "analysis_focus": analysis_focus,
        "search_query": search_query,
        "connector_id": connector_id,
        "connector_consent_state": connector_consent_state,
        "external_context_used": external_context_used,
        "external_match_count": external_match_count,
        "selected_external_resource_snapshot_id": selected_external_resource_snapshot_id,
        "external_resource_snapshot_id": external_resource_snapshot_id,
        "mcp_server_id": mcp_server_id,
        "mcp_resource_id": mcp_resource_id,
        "mcp_tool_name": mcp_tool_name,
        "mcp_prompt_name": mcp_prompt_name,
        "mcp_transport": mcp_transport,
        "mcp_read_status": mcp_read_status,
        "context_selection_mode": context_selection_mode,
        "source_titles": source_titles,
    }


def get_ai_frontier_research_record(*, record_id: str, user_id: str) -> AiFrontierResearchRecordResponse | None:
    record = ai_frontier_research_record_repository.get_ai_frontier_research_record_for_user(record_id, user_id)
    if record is None:
        return None
    return AiFrontierResearchRecordResponse.from_model(record)


def get_ai_frontier_research_record_for_run(run_id: str) -> AiFrontierResearchRecordResponse | None:
    record = ai_frontier_research_record_repository.get_ai_frontier_research_record_by_source_run_id(run_id)
    if record is None:
        return None
    return AiFrontierResearchRecordResponse.from_model(record)


def list_workspace_ai_frontier_research_records(
    *,
    workspace_id: str,
    user_id: str,
    limit: int = 12,
) -> list[AiFrontierResearchRecordResponse]:
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise AiFrontierResearchRecordAccessError("Workspace not found")
    runs = ai_frontier_research_record_repository.list_workspace_ai_frontier_research_records(
        workspace_id=workspace_id,
        user_id=user_id,
        limit=max(1, min(limit, 20)),
    )
    return [AiFrontierResearchRecordResponse.from_model(record) for record in runs]


def save_ai_frontier_research_record(
    *,
    workspace_id: str,
    user_id: str,
    payload: AiFrontierResearchRecordWriteRequest,
) -> AiFrontierResearchRecordResponse:
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise AiFrontierResearchRecordAccessError("Workspace not found")

    return create_ai_frontier_research_record(
        workspace_id=workspace_id,
        user_id=user_id,
        title=payload.title,
        conversation_id=payload.conversation_id,
        source_run_id=None,
        source_trace_id=payload.source_trace_id,
        question=payload.question,
        answer_text=payload.answer_text,
        output=payload.output,
        follow_ups=payload.follow_ups,
        source_set=payload.source_set,
    )


def update_ai_frontier_research_record(
    *,
    record_id: str,
    user_id: str,
    payload: AiFrontierResearchRecordWriteRequest,
) -> AiFrontierResearchRecordResponse | None:
    persisted_source_set = dict(payload.source_set)
    if payload.answer_text:
        persisted_source_set["answer_text"] = payload.answer_text
    persisted_source_set["follow_ups"] = [
        follow_up.model_dump(mode="json") for follow_up in payload.follow_ups
    ]

    record = ai_frontier_research_record_repository.update_ai_frontier_research_record(
        record_id=record_id,
        user_id=user_id,
        title=_build_record_title(payload.title, payload.question),
        question=payload.question,
        frontier_summary=payload.output.frontier_summary,
        trend_judgment=payload.output.trend_judgment,
        themes_json=[theme.model_dump() for theme in payload.output.themes],
        events_json=[event.model_dump() for event in payload.output.events],
        project_cards_json=[card.model_dump() for card in payload.output.project_cards],
        reference_sources_json=[reference.model_dump() for reference in payload.output.reference_sources],
        source_set_json=persisted_source_set,
    )
    if record is None:
        return None
    return AiFrontierResearchRecordResponse.from_model(record)


def delete_ai_frontier_research_record(*, record_id: str, user_id: str) -> bool:
    return ai_frontier_research_record_repository.delete_ai_frontier_research_record(
        record_id=record_id,
        user_id=user_id,
    )
