from dataclasses import dataclass, field
from typing import Literal

from app.connectors.research_external_context_connector import ResearchExternalContextEntry
from app.schemas.chat import ChatToolStep, SourceReference
from app.schemas.mcp import (
    RESEARCH_CONTEXT_DIGEST_RESOURCE_DISPLAY_NAME,
    RESEARCH_CONTEXT_DIGEST_RESOURCE_ID,
    RESEARCH_CONTEXT_DIGEST_RESOURCE_URI,
    RESEARCH_CONTEXT_LOCAL_MCP_SERVER_ID,
)
from app.schemas.research_external_resource_snapshot import ResearchExternalResourceSnapshotResponse
from app.services.connector_service import (
    RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
    ConnectorConsentRequiredError,
    require_workspace_connector_consent,
)
from app.services.mcp_service import McpValidationError, read_workspace_mcp_resource
from app.services.model_interface_service import ModelInterfaceError, ModelMessage
from app.services.research_external_resource_snapshot_service import (
    deserialize_research_external_resource_snapshot_matches,
)
from app.services.research_tool_assisted_chat_service import (
    ResearchRunMemoryContext,
    ToolAssistedResearchChatResult,
    run_tool_assisted_research_chat,
)
from app.services.retrieval_generation_service import ChatProcessingError, get_chat_model_interface

_MAX_EXTERNAL_MATCHES = 3


@dataclass(slots=True)
class ResearchExternalContextChatResult:
    answer: str
    prompt: str
    sources: list[SourceReference]
    tool_steps: list[ChatToolStep]
    token_input: int
    token_output: int
    analysis_focus: str | None = None
    search_query: str | None = None
    degraded_reason: str | None = None
    connector_id: str = RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID
    connector_consent_state: str = "not_granted"
    external_context_used: bool = False
    external_match_count: int = 0
    external_matches: list[ResearchExternalContextEntry] = field(default_factory=list)
    selected_external_resource_snapshot_id: str | None = None
    mcp_server_id: str | None = None
    mcp_resource_id: str | None = None
    mcp_resource_uri: str | None = None
    mcp_resource_display_name: str | None = None
    context_selection_mode: Literal["none", "snapshot", "mcp_resource"] = "none"


def _append_answer_note(answer: str, note: str) -> str:
    stripped_answer = answer.strip()
    stripped_note = note.strip()
    if not stripped_answer:
        return stripped_note
    return f"{stripped_answer}\n\n{stripped_note}"


def _serialize_external_sources(matches: list[ResearchExternalContextEntry]) -> list[SourceReference]:
    return [
        SourceReference(
            document_id=f"external:{match.context_id}",
            chunk_id=f"external:{match.context_id}",
            document_title=match.title,
            chunk_index=0,
            snippet=match.snippet,
            source_kind="external_context",
        )
        for match in matches
    ]


def _summarize_mcp_resource_step(
    *,
    match_count: int,
    search_query: str,
    resource_display_name: str,
    resource_uri: str,
) -> ChatToolStep:
    return ChatToolStep(
        tool_name="research_external_context",
        summary=f"已通过 MCP 资源“{resource_display_name}”读取 {match_count} 条外部上下文。",
        detail=f"资源 URI：{resource_uri}；搜索词：{search_query}",
    )


def _summarize_selected_snapshot_step(
    *,
    snapshot: ResearchExternalResourceSnapshotResponse,
) -> ChatToolStep:
    return ChatToolStep(
        tool_name="research_external_context",
        summary=f"已显式复用外部资源快照“{snapshot.title}”。",
        detail=f"这次直接使用 {snapshot.resource_count} 条已保存资源，而不是重新读取 MCP 资源。",
    )


def _summarize_external_context_degraded_step(*, reason: str) -> ChatToolStep:
    if reason == "connector_consent_required":
        return ChatToolStep(
            tool_name="research_external_context",
            summary="这次没有使用 MCP 资源，因为当前工作区还没有完成授权。",
            detail="先授权当前工作区，再继续运行 MCP 资源试点。",
        )
    if reason == "connector_consent_revoked":
        return ChatToolStep(
            tool_name="research_external_context",
            summary="这次没有使用 MCP 资源，因为当前工作区已经撤销了授权。",
            detail="重新授权后，才能继续使用外部资源快照或新的 MCP 上下文。",
        )
    if reason == "external_context_unavailable":
        return ChatToolStep(
            tool_name="research_external_context",
            summary="MCP 资源当前暂时不可用。",
            detail="系统已经诚实降级到只使用工作区资料的路径。",
        )
    if reason == "selected_external_resource_snapshot_empty":
        return ChatToolStep(
            tool_name="research_external_context",
            summary="选中的外部资源快照里没有可用内容。",
            detail="请重新选择一个最近快照，或改成自动读取 MCP 资源。",
        )
    return ChatToolStep(
        tool_name="research_external_context",
        summary="MCP 资源没有命中足够有用的外部上下文。",
        detail="系统已经诚实降级到只使用工作区资料的路径。",
    )


def _build_internal_source_block(sources: list[SourceReference]) -> str:
    if not sources:
        return "No grounded workspace-document evidence was found."
    return "\n\n".join(
        (
            f"[Workspace document | {source.document_title} | chunk {source.chunk_index} | {source.chunk_id}]\n"
            f"{source.snippet}"
        )
        for source in sources
    )


def _build_external_source_block(matches: list[ResearchExternalContextEntry]) -> str:
    if not matches:
        return "No approved external context was available."
    return "\n\n".join(
        (
            f"[External context | {match.source_label} | {match.title}]\n"
            f"{match.snippet}"
        )
        for match in matches
    )


def _build_external_context_prompt(
    *,
    question: str,
    internal_result: ToolAssistedResearchChatResult,
    external_matches: list[ResearchExternalContextEntry],
) -> str:
    return (
        f"User question:\n{question}\n\n"
        f"Existing bounded Research answer from workspace material:\n{internal_result.answer}\n\n"
        f"Analysis focus:\n{internal_result.analysis_focus or question}\n\n"
        f"Search query used:\n{internal_result.search_query or question}\n\n"
        f"Workspace-grounded evidence:\n{_build_internal_source_block(internal_result.sources)}\n\n"
        f"Approved external context:\n{_build_external_source_block(external_matches)}\n\n"
        "Write one practical answer in the same language as the user. "
        "Keep workspace-grounded evidence and external context visibly distinct. "
        "State: 1) the current conclusion, 2) what is supported by workspace material, "
        "3) what comes from external context, and 4) what still needs verification."
    )


def _synthesize_external_context_answer(
    *,
    question: str,
    internal_result: ToolAssistedResearchChatResult,
    external_matches: list[ResearchExternalContextEntry],
) -> tuple[str, str, int, int]:
    prompt = _build_external_context_prompt(
        question=question,
        internal_result=internal_result,
        external_matches=external_matches,
    )
    try:
        response = get_chat_model_interface().generate_text(
            temperature=0.2,
            messages=[
                ModelMessage(
                    role="system",
                    content=(
                        "You are running a bounded Research MCP resource pilot. "
                        "Use the provided workspace material and the approved external context only. "
                        "Keep the two evidence classes visibly distinct and do not invent extra sources."
                    ),
                ),
                ModelMessage(role="user", content=prompt),
            ],
        )
    except ModelInterfaceError as error:
        raise ChatProcessingError("Failed to generate the MCP-backed research answer") from error

    answer = response.text.strip()
    if not answer:
        raise ChatProcessingError("MCP-backed research analysis returned an empty answer")
    return answer, prompt, response.usage.input_tokens, response.usage.output_tokens


def _convert_mcp_items_to_matches(mcp_items) -> list[ResearchExternalContextEntry]:
    return [
        ResearchExternalContextEntry(
            context_id=item.resource_id,
            title=item.title,
            source_label=item.source_label,
            keywords=(),
            snippet=item.snippet,
        )
        for item in mcp_items
    ]


def run_research_external_context_chat(
    *,
    workspace_id: str,
    user_id: str,
    question: str,
    prior_memory: ResearchRunMemoryContext | None = None,
    selected_external_resource_snapshot: ResearchExternalResourceSnapshotResponse | None = None,
) -> ResearchExternalContextChatResult:
    internal_result = run_tool_assisted_research_chat(
        workspace_id=workspace_id,
        user_id=user_id,
        question=question,
        prior_memory=prior_memory,
    )

    tool_steps = list(internal_result.tool_steps)
    search_query = internal_result.search_query or question.strip()
    selection_mode: Literal["none", "snapshot", "mcp_resource"] = (
        "snapshot" if selected_external_resource_snapshot is not None else "mcp_resource"
    )

    try:
        require_workspace_connector_consent(
            workspace_id=workspace_id,
            user_id=user_id,
            connector_id=RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
        )
    except ConnectorConsentRequiredError as error:
        degraded_reason = (
            "connector_consent_revoked"
            if getattr(error, "consent_state", "not_granted") == "revoked"
            else "connector_consent_required"
        )
        tool_steps.append(_summarize_external_context_degraded_step(reason=degraded_reason))
        answer_note = (
            "这次没有使用 MCP 资源，因为当前工作区已经撤销了当前连接器授权。"
            if degraded_reason == "connector_consent_revoked"
            else "这次没有使用 MCP 资源，因为当前工作区还没有为这个试点完成授权。"
        )
        return ResearchExternalContextChatResult(
            answer=_append_answer_note(internal_result.answer, answer_note),
            prompt=internal_result.prompt,
            sources=internal_result.sources,
            tool_steps=tool_steps,
            token_input=internal_result.token_input,
            token_output=internal_result.token_output,
            analysis_focus=internal_result.analysis_focus,
            search_query=search_query,
            degraded_reason=degraded_reason,
            connector_consent_state=getattr(error, "consent_state", "not_granted"),
            external_context_used=False,
            external_match_count=0,
            external_matches=[],
            selected_external_resource_snapshot_id=(
                selected_external_resource_snapshot.id if selected_external_resource_snapshot else None
            ),
            mcp_server_id=RESEARCH_CONTEXT_LOCAL_MCP_SERVER_ID,
            mcp_resource_id=RESEARCH_CONTEXT_DIGEST_RESOURCE_ID,
            mcp_resource_uri=RESEARCH_CONTEXT_DIGEST_RESOURCE_URI,
            mcp_resource_display_name=RESEARCH_CONTEXT_DIGEST_RESOURCE_DISPLAY_NAME,
            context_selection_mode=selection_mode,
        )

    if selected_external_resource_snapshot is not None:
        external_matches = deserialize_research_external_resource_snapshot_matches(selected_external_resource_snapshot)
        if not external_matches:
            degraded_reason = "selected_external_resource_snapshot_empty"
            tool_steps.append(_summarize_external_context_degraded_step(reason=degraded_reason))
            return ResearchExternalContextChatResult(
                answer=_append_answer_note(
                    internal_result.answer,
                    "这次选中的外部资源快照里没有可用内容，所以答案只反映当前工作区资料。",
                ),
                prompt=internal_result.prompt,
                sources=internal_result.sources,
                tool_steps=tool_steps,
                token_input=internal_result.token_input,
                token_output=internal_result.token_output,
                analysis_focus=internal_result.analysis_focus,
                search_query=selected_external_resource_snapshot.search_query,
                degraded_reason=degraded_reason,
                connector_consent_state="granted",
                external_context_used=False,
                external_match_count=0,
                external_matches=[],
                selected_external_resource_snapshot_id=selected_external_resource_snapshot.id,
                context_selection_mode="snapshot",
            )

        tool_steps.append(_summarize_selected_snapshot_step(snapshot=selected_external_resource_snapshot))
        answer, prompt, synthesis_input_tokens, synthesis_output_tokens = _synthesize_external_context_answer(
            question=question,
            internal_result=internal_result,
            external_matches=external_matches,
        )
        return ResearchExternalContextChatResult(
            answer=answer,
            prompt=prompt,
            sources=[*internal_result.sources, *_serialize_external_sources(external_matches)],
            tool_steps=tool_steps,
            token_input=internal_result.token_input + synthesis_input_tokens,
            token_output=internal_result.token_output + synthesis_output_tokens,
            analysis_focus=internal_result.analysis_focus,
            search_query=selected_external_resource_snapshot.search_query,
            degraded_reason=None,
            connector_consent_state="granted",
            external_context_used=True,
            external_match_count=len(external_matches),
            external_matches=external_matches,
            selected_external_resource_snapshot_id=selected_external_resource_snapshot.id,
            context_selection_mode="snapshot",
        )

    try:
        mcp_result = read_workspace_mcp_resource(
            workspace_id=workspace_id,
            user_id=user_id,
            connector_id=RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
            resource_id=RESEARCH_CONTEXT_DIGEST_RESOURCE_ID,
            query=search_query,
            limit=_MAX_EXTERNAL_MATCHES,
        )
    except McpValidationError:
        degraded_reason = "external_context_unavailable"
        tool_steps.append(_summarize_external_context_degraded_step(reason=degraded_reason))
        return ResearchExternalContextChatResult(
            answer=_append_answer_note(
                internal_result.answer,
                "这次 MCP 资源暂时不可用，所以答案只反映当前工作区资料。",
            ),
            prompt=internal_result.prompt,
            sources=internal_result.sources,
            tool_steps=tool_steps,
            token_input=internal_result.token_input,
            token_output=internal_result.token_output,
            analysis_focus=internal_result.analysis_focus,
            search_query=search_query,
            degraded_reason=degraded_reason,
            connector_consent_state="granted",
            external_context_used=False,
            external_match_count=0,
            external_matches=[],
            mcp_server_id=RESEARCH_CONTEXT_LOCAL_MCP_SERVER_ID,
            mcp_resource_id=RESEARCH_CONTEXT_DIGEST_RESOURCE_ID,
            mcp_resource_uri=RESEARCH_CONTEXT_DIGEST_RESOURCE_URI,
            mcp_resource_display_name=RESEARCH_CONTEXT_DIGEST_RESOURCE_DISPLAY_NAME,
            context_selection_mode="mcp_resource",
        )

    external_matches = _convert_mcp_items_to_matches(mcp_result.items)
    if not external_matches:
        degraded_reason = "external_context_no_useful_matches"
        tool_steps.append(_summarize_external_context_degraded_step(reason=degraded_reason))
        return ResearchExternalContextChatResult(
            answer=_append_answer_note(
                internal_result.answer,
                "这次 MCP 资源没有命中足够有用的补充内容，所以答案只反映当前工作区资料。",
            ),
            prompt=internal_result.prompt,
            sources=internal_result.sources,
            tool_steps=tool_steps,
            token_input=internal_result.token_input,
            token_output=internal_result.token_output,
            analysis_focus=internal_result.analysis_focus,
            search_query=search_query,
            degraded_reason=degraded_reason,
            connector_consent_state="granted",
            external_context_used=False,
            external_match_count=0,
            external_matches=[],
            mcp_server_id=mcp_result.server.id,
            mcp_resource_id=mcp_result.resource.id,
            mcp_resource_uri=mcp_result.resource.uri,
            mcp_resource_display_name=mcp_result.resource.display_name,
            context_selection_mode="mcp_resource",
        )

    tool_steps.append(
        _summarize_mcp_resource_step(
            match_count=len(external_matches),
            search_query=search_query,
            resource_display_name=mcp_result.resource.display_name,
            resource_uri=mcp_result.resource.uri,
        )
    )
    answer, prompt, synthesis_input_tokens, synthesis_output_tokens = _synthesize_external_context_answer(
        question=question,
        internal_result=internal_result,
        external_matches=external_matches,
    )
    return ResearchExternalContextChatResult(
        answer=answer,
        prompt=prompt,
        sources=[*internal_result.sources, *_serialize_external_sources(external_matches)],
        tool_steps=tool_steps,
        token_input=internal_result.token_input + synthesis_input_tokens,
        token_output=internal_result.token_output + synthesis_output_tokens,
        analysis_focus=internal_result.analysis_focus,
        search_query=search_query,
        degraded_reason=None,
        connector_consent_state="granted",
        external_context_used=True,
        external_match_count=len(external_matches),
        external_matches=external_matches,
        mcp_server_id=mcp_result.server.id,
        mcp_resource_id=mcp_result.resource.id,
        mcp_resource_uri=mcp_result.resource.uri,
        mcp_resource_display_name=mcp_result.resource.display_name,
        context_selection_mode="mcp_resource",
    )
