from dataclasses import dataclass, field
from typing import Any, Literal

from app.connectors.research_external_context_connector import ResearchExternalContextEntry
from app.schemas.ai_frontier_research import AiFrontierResearchOutput
from app.schemas.chat import ChatToolStep, SourceReference
from app.schemas.mcp import (
    AI_FRONTIER_BRIEF_PROMPT_NAME,
    AI_FRONTIER_DIGEST_RESOURCE_DISPLAY_NAME,
    AI_FRONTIER_DIGEST_RESOURCE_ID,
    AI_FRONTIER_DIGEST_RESOURCE_URI,
    AI_FRONTIER_EXTERNAL_MCP_SERVER_ID,
    AI_FRONTIER_SEARCH_TOOL_NAME,
    McpEndpointAuthState,
    RemoteMcpReadStatus,
)
from app.schemas.research_external_resource_snapshot import ResearchExternalResourceSnapshotResponse
from app.services.ai_frontier_research_output_service import build_ai_frontier_research_output
from app.services.connector_service import (
    RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
    ConnectorConsentRequiredError,
    require_workspace_connector_consent,
)
from app.services.mcp_service import (
    McpExternalEndpointNotConfiguredError,
    McpRemoteAuthDeniedError,
    McpRemoteAuthRequiredError,
    McpRemoteTransportError,
    McpValidationError,
    call_workspace_true_external_mcp_tool,
    describe_workspace_true_external_mcp_endpoint,
    get_workspace_true_external_mcp_prompt,
    read_workspace_true_external_mcp_resource,
)
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

_MAX_EXTERNAL_MATCHES = 5
_DIGEST_SNIPPET_LIMIT = 800


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
    mcp_tool_name: str | None = None
    mcp_prompt_name: str | None = None
    mcp_transport: str | None = None
    mcp_read_status: RemoteMcpReadStatus | None = None
    mcp_transport_error: str | None = None
    mcp_endpoint_source: str | None = None
    mcp_endpoint_display_name: str | None = None
    mcp_endpoint_auth_state: McpEndpointAuthState | None = None
    mcp_endpoint_auth_detail: str | None = None
    context_selection_mode: Literal["none", "snapshot", "mcp_resource"] = "none"
    frontier_output: AiFrontierResearchOutput | None = None
    tool_structured_content: dict[str, Any] | None = None


def _finalize_research_external_context_result(
    **kwargs: Any,
) -> ResearchExternalContextChatResult:
    external_matches = kwargs.get("external_matches") or []
    tool_structured_content = kwargs.pop("tool_structured_content", None)
    return ResearchExternalContextChatResult(
        frontier_output=build_ai_frontier_research_output(
            answer=kwargs["answer"],
            analysis_focus=kwargs.get("analysis_focus"),
            search_query=kwargs.get("search_query"),
            degraded_reason=kwargs.get("degraded_reason"),
            external_matches=external_matches,
            tool_structured_content=tool_structured_content,
        ),
        tool_structured_content=tool_structured_content,
        **kwargs,
    )


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


def _serialize_digest_source(*, resource_id: str, resource_title: str, text: str) -> SourceReference | None:
    snippet = text.strip()
    if not snippet:
        return None
    if len(snippet) > _DIGEST_SNIPPET_LIMIT:
        snippet = snippet[:_DIGEST_SNIPPET_LIMIT].rstrip() + "..."
    return SourceReference(
        document_id=f"mcp:{resource_id}",
        chunk_id=f"mcp:{resource_id}",
        document_title=resource_title,
        chunk_index=0,
        snippet=snippet,
        source_kind="external_context",
    )


def _summarize_mcp_resource_step(
    *,
    resource_display_name: str,
    resource_uri: str,
) -> ChatToolStep:
    return ChatToolStep(
        tool_name="mcp_resource",
        summary=f"已读取 MCP 资源“{resource_display_name}”。",
        detail=f"资源 URI：{resource_uri}",
    )


def _summarize_mcp_tool_step(
    *,
    search_query: str,
    match_count: int,
) -> ChatToolStep:
    return ChatToolStep(
        tool_name="mcp_tool",
        summary=f"已调用 MCP 工具“{AI_FRONTIER_SEARCH_TOOL_NAME}”，命中 {match_count} 个项目或事件。",
        detail=f"搜索词：{search_query}",
    )


def _summarize_mcp_prompt_step(*, topic: str) -> ChatToolStep:
    return ChatToolStep(
        tool_name="mcp_prompt",
        summary=f"已获取 MCP 提示“{AI_FRONTIER_BRIEF_PROMPT_NAME}”。",
        detail=f"主题：{topic}",
    )


def _summarize_selected_snapshot_step(
    *,
    snapshot: ResearchExternalResourceSnapshotResponse,
) -> ChatToolStep:
    return ChatToolStep(
        tool_name="research_external_context",
        summary=f"已复用外部资源快照“{snapshot.title}”。",
        detail=f"这次直接使用 {snapshot.resource_count} 条已保存项目，不再重新读取外部 MCP 资源。",
    )


def _summarize_external_context_degraded_step(
    *,
    reason: str,
    transport_error: str | None = None,
    auth_state: McpEndpointAuthState | None = None,
) -> ChatToolStep:
    if reason == "connector_consent_required":
        return ChatToolStep(
            tool_name="research_external_context",
            summary="这次没有使用外部 MCP 资源，因为当前工作区还没有完成授权。",
            detail="先为当前工作区授权，再继续运行 AI 前沿研究外部信息路径。",
        )
    if reason == "connector_consent_revoked":
        return ChatToolStep(
            tool_name="research_external_context",
            summary="这次没有使用外部 MCP 资源，因为当前工作区已经撤销授权。",
            detail="重新授权后，才能继续使用外部资源快照或新的 MCP 上下文。",
        )
    if reason == "selected_external_resource_snapshot_empty":
        return ChatToolStep(
            tool_name="research_external_context",
            summary="选中的外部资源快照里没有可用内容。",
            detail="请重新选择一个最近快照，或改成重新读取 MCP 资源。",
        )
    if reason == "external_context_auth_required":
        return ChatToolStep(
            tool_name="research_external_context",
            summary="远程 MCP 端点要求认证，但当前还没有可用凭据。",
            detail="补齐外部 MCP 认证配置后，才能继续读取远程上下文。",
        )
    if reason == "external_context_auth_denied":
        return ChatToolStep(
            tool_name="research_external_context",
            summary="远程 MCP 端点拒绝了当前凭据。",
            detail="请检查外部 MCP 认证配置，系统已诚实降级到只使用工作区资料。",
        )
    if reason == "external_context_unavailable":
        detail = "系统已诚实降级到只使用工作区资料的路径。"
        if auth_state == "missing":
            detail = "当前外部 MCP 端点要求认证，但服务端还没有配置令牌，因此系统已诚实降级。"
        if transport_error:
            detail = f"{detail} 远程细节：{transport_error}"
        return ChatToolStep(
            tool_name="research_external_context",
            summary="远程 MCP 资源当前暂时不可用。",
            detail=detail,
        )
    return ChatToolStep(
        tool_name="research_external_context",
        summary="远程 MCP 工具没有命中足够有用的项目或事件。",
        detail="系统仍保留了 MCP 摘要资源，但没有额外项目卡片可供展开。",
    )


def _build_internal_source_block(sources: list[SourceReference]) -> str:
    if not sources:
        return "没有找到工作区内部资料。"
    return "\n\n".join(
        (
            f"[工作区资料 | {source.document_title} | chunk {source.chunk_index} | {source.chunk_id}]\n"
            f"{source.snippet}"
        )
        for source in sources
    )


def _build_external_project_block(matches: list[ResearchExternalContextEntry]) -> str:
    if not matches:
        return "没有额外项目卡片。"
    return "\n\n".join(
        (
            f"[项目或事件 | {match.source_label} | {match.title}]\n"
            f"{match.snippet}"
        )
        for match in matches
    )


def _build_external_context_prompt(
    *,
    question: str,
    internal_result: ToolAssistedResearchChatResult,
    digest_text: str,
    brief_prompt: str,
    external_matches: list[ResearchExternalContextEntry],
) -> str:
    return (
        f"用户问题：\n{question}\n\n"
        f"工作区内部分析结果：\n{internal_result.answer}\n\n"
        f"分析焦点：\n{internal_result.analysis_focus or question}\n\n"
        f"搜索词：\n{internal_result.search_query or question}\n\n"
        f"工作区资料：\n{_build_internal_source_block(internal_result.sources)}\n\n"
        f"MCP 摘要资源：\n{digest_text}\n\n"
        f"MCP 提示模板：\n{brief_prompt}\n\n"
        f"MCP 工具项目结果：\n{_build_external_project_block(external_matches)}\n\n"
        "请用与用户相同的语言给出一份实用回答。"
        "必须明确区分：1）基于工作区资料的判断；2）基于外部 MCP 摘要资源的判断；"
        "3）基于 MCP 工具项目结果的项目卡片或事件卡片；4）还需要继续验证的点。"
        "引用来源时请把链接放进独立的参考来源区，不要把一堆链接塞进主段落。"
    )


def _synthesize_external_context_answer(
    *,
    question: str,
    internal_result: ToolAssistedResearchChatResult,
    digest_text: str,
    brief_prompt: str,
    external_matches: list[ResearchExternalContextEntry],
) -> tuple[str, str, int, int]:
    prompt = _build_external_context_prompt(
        question=question,
        internal_result=internal_result,
        digest_text=digest_text,
        brief_prompt=brief_prompt,
        external_matches=external_matches,
    )
    try:
        response = get_chat_model_interface().generate_text(
            temperature=0.2,
            messages=[
                ModelMessage(
                    role="system",
                    content=(
                        "你正在运行一条 MCP 驱动的 AI 前沿研究路径。"
                        "你只能使用提供的工作区资料、MCP 摘要资源、MCP 工具结果和 MCP 提示模板。"
                        "结论要清楚，来源要可追溯，链接要集中放在参考来源区。"
                    ),
                ),
                ModelMessage(role="user", content=prompt),
            ],
        )
    except ModelInterfaceError as error:
        raise ChatProcessingError("Failed to generate the MCP-backed AI frontier answer") from error

    answer = response.text.strip()
    if not answer:
        raise ChatProcessingError("MCP-backed AI frontier analysis returned an empty answer")
    return answer, prompt, response.usage.input_tokens, response.usage.output_tokens


def _convert_mcp_tool_items_to_matches(structured_content: dict[str, Any] | None) -> list[ResearchExternalContextEntry]:
    if not structured_content:
        return []
    raw_items = structured_content.get("items")
    if not isinstance(raw_items, list):
        return []

    matches: list[ResearchExternalContextEntry] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        item_id = item.get("id")
        title = item.get("title")
        source_label = item.get("source_label")
        summary = item.get("summary")
        why_it_matters = item.get("why_it_matters")
        source_url = item.get("source_url")
        repo_url = item.get("repo_url")
        docs_url = item.get("docs_url")
        if not isinstance(item_id, str) or not isinstance(title, str) or not isinstance(source_label, str):
            continue
        summary_text = summary if isinstance(summary, str) else ""
        why_text = why_it_matters if isinstance(why_it_matters, str) else ""
        links = [
            f"官网：{source_url}" if isinstance(source_url, str) and source_url else "",
            f"仓库：{repo_url}" if isinstance(repo_url, str) and repo_url else "",
            f"文档：{docs_url}" if isinstance(docs_url, str) and docs_url else "",
        ]
        snippet_parts = [part for part in [summary_text, f"为什么重要：{why_text}" if why_text else "", *links] if part]
        matches.append(
            ResearchExternalContextEntry(
                context_id=item_id,
                title=title,
                source_label=source_label,
                keywords=(),
                snippet="\n".join(snippet_parts),
            )
        )
    return matches


def _build_endpoint_state(
    *,
    workspace_id: str,
    user_id: str,
) -> tuple[str | None, str | None, McpEndpointAuthState | None, str | None]:
    endpoint, auth_state, auth_detail = describe_workspace_true_external_mcp_endpoint(
        workspace_id=workspace_id,
        user_id=user_id,
        connector_id=RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
    )
    return (
        endpoint.source if endpoint is not None else None,
        endpoint.display_name if endpoint is not None else None,
        auth_state,
        auth_detail,
    )


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
    endpoint_source, endpoint_display_name, endpoint_auth_state, endpoint_auth_detail = _build_endpoint_state(
        workspace_id=workspace_id,
        user_id=user_id,
    )
    tool_steps = list(internal_result.tool_steps)
    search_query = internal_result.search_query or question.strip()
    prompt_topic = internal_result.analysis_focus or question.strip()
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
            "这次没有使用外部 MCP 资源，因为当前工作区已经撤销了授权。"
            if degraded_reason == "connector_consent_revoked"
            else "这次没有使用外部 MCP 资源，因为当前工作区还没有完成授权。"
        )
        return _finalize_research_external_context_result(
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
            mcp_server_id=AI_FRONTIER_EXTERNAL_MCP_SERVER_ID,
            mcp_resource_id=AI_FRONTIER_DIGEST_RESOURCE_ID,
            mcp_resource_uri=AI_FRONTIER_DIGEST_RESOURCE_URI,
            mcp_resource_display_name=AI_FRONTIER_DIGEST_RESOURCE_DISPLAY_NAME,
            mcp_tool_name=AI_FRONTIER_SEARCH_TOOL_NAME,
            mcp_prompt_name=AI_FRONTIER_BRIEF_PROMPT_NAME,
            mcp_transport="stdio_process",
            mcp_read_status=("consent_revoked" if degraded_reason == "connector_consent_revoked" else "consent_required"),
            mcp_endpoint_source=endpoint_source,
            mcp_endpoint_display_name=endpoint_display_name,
            mcp_endpoint_auth_state=endpoint_auth_state,
            mcp_endpoint_auth_detail=endpoint_auth_detail,
            context_selection_mode=selection_mode,
        )

    if selected_external_resource_snapshot is not None:
        external_matches = deserialize_research_external_resource_snapshot_matches(selected_external_resource_snapshot)
        if not external_matches:
            degraded_reason = "selected_external_resource_snapshot_empty"
            tool_steps.append(_summarize_external_context_degraded_step(reason=degraded_reason))
            return _finalize_research_external_context_result(
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
                mcp_tool_name=AI_FRONTIER_SEARCH_TOOL_NAME,
                mcp_prompt_name=AI_FRONTIER_BRIEF_PROMPT_NAME,
                mcp_transport="stdio_process",
                mcp_read_status="snapshot_reused",
                mcp_endpoint_source=endpoint_source,
                mcp_endpoint_display_name=endpoint_display_name,
                mcp_endpoint_auth_state=endpoint_auth_state,
                mcp_endpoint_auth_detail=endpoint_auth_detail,
                context_selection_mode="snapshot",
            )

        tool_steps.append(_summarize_selected_snapshot_step(snapshot=selected_external_resource_snapshot))
        answer, prompt, synthesis_input_tokens, synthesis_output_tokens = _synthesize_external_context_answer(
            question=question,
            internal_result=internal_result,
            digest_text="本次直接复用了外部资源快照，没有重新读取 MCP 摘要资源。",
            brief_prompt="本次直接复用了外部资源快照，没有重新获取 MCP 提示。",
            external_matches=external_matches,
        )
        return _finalize_research_external_context_result(
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
            mcp_tool_name=AI_FRONTIER_SEARCH_TOOL_NAME,
            mcp_prompt_name=AI_FRONTIER_BRIEF_PROMPT_NAME,
            mcp_transport="stdio_process",
            mcp_read_status="snapshot_reused",
            mcp_endpoint_source=endpoint_source,
            mcp_endpoint_display_name=endpoint_display_name,
            mcp_endpoint_auth_state=endpoint_auth_state,
            mcp_endpoint_auth_detail=endpoint_auth_detail,
            context_selection_mode="snapshot",
            tool_structured_content=None,
        )

    try:
        mcp_resource = read_workspace_true_external_mcp_resource(
            workspace_id=workspace_id,
            user_id=user_id,
            connector_id=RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
            resource_id=AI_FRONTIER_DIGEST_RESOURCE_ID,
            query=search_query,
            limit=1,
        )
        mcp_prompt = get_workspace_true_external_mcp_prompt(
            workspace_id=workspace_id,
            user_id=user_id,
            connector_id=RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
            prompt_name=AI_FRONTIER_BRIEF_PROMPT_NAME,
            arguments={"topic": prompt_topic, "include_projects": "true"},
        )
        mcp_tool = call_workspace_true_external_mcp_tool(
            workspace_id=workspace_id,
            user_id=user_id,
            connector_id=RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
            tool_name=AI_FRONTIER_SEARCH_TOOL_NAME,
            arguments={"query": search_query, "limit": _MAX_EXTERNAL_MATCHES},
        )
    except McpExternalEndpointNotConfiguredError as error:
        degraded_reason = "external_context_unavailable"
        tool_steps.append(
            _summarize_external_context_degraded_step(
                reason=degraded_reason,
                transport_error=str(error),
                auth_state=endpoint_auth_state,
            )
        )
        return _finalize_research_external_context_result(
            answer=_append_answer_note(
                internal_result.answer,
                "这次没有使用外部 MCP 上下文，因为当前还没有配置可用的独立 MCP 服务端。",
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
            mcp_server_id=AI_FRONTIER_EXTERNAL_MCP_SERVER_ID,
            mcp_resource_id=AI_FRONTIER_DIGEST_RESOURCE_ID,
            mcp_resource_uri=AI_FRONTIER_DIGEST_RESOURCE_URI,
            mcp_resource_display_name=AI_FRONTIER_DIGEST_RESOURCE_DISPLAY_NAME,
            mcp_tool_name=AI_FRONTIER_SEARCH_TOOL_NAME,
            mcp_prompt_name=AI_FRONTIER_BRIEF_PROMPT_NAME,
            mcp_transport="stdio_process",
            mcp_read_status="transport_unavailable",
            mcp_transport_error=str(error),
            mcp_endpoint_source=endpoint_source,
            mcp_endpoint_display_name=endpoint_display_name,
            mcp_endpoint_auth_state=endpoint_auth_state,
            mcp_endpoint_auth_detail=endpoint_auth_detail,
            context_selection_mode="mcp_resource",
            tool_structured_content=None,
        )
    except McpRemoteAuthRequiredError as error:
        degraded_reason = "external_context_auth_required"
        tool_steps.append(
            _summarize_external_context_degraded_step(
                reason=degraded_reason,
                transport_error=str(error),
                auth_state="missing",
            )
        )
        return _finalize_research_external_context_result(
            answer=_append_answer_note(
                internal_result.answer,
                "这次没有使用远程 MCP 上下文，因为当前端点要求认证，但服务端还没有配置可用凭据。",
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
            mcp_server_id=AI_FRONTIER_EXTERNAL_MCP_SERVER_ID,
            mcp_resource_id=AI_FRONTIER_DIGEST_RESOURCE_ID,
            mcp_resource_uri=AI_FRONTIER_DIGEST_RESOURCE_URI,
            mcp_resource_display_name=AI_FRONTIER_DIGEST_RESOURCE_DISPLAY_NAME,
            mcp_tool_name=AI_FRONTIER_SEARCH_TOOL_NAME,
            mcp_prompt_name=AI_FRONTIER_BRIEF_PROMPT_NAME,
            mcp_transport="stdio_process",
            mcp_read_status="auth_required",
            mcp_transport_error=str(error),
            mcp_endpoint_source=endpoint_source,
            mcp_endpoint_display_name=endpoint_display_name,
            mcp_endpoint_auth_state="missing",
            mcp_endpoint_auth_detail=str(error),
            context_selection_mode="mcp_resource",
        )
    except McpRemoteAuthDeniedError as error:
        degraded_reason = "external_context_auth_denied"
        tool_steps.append(
            _summarize_external_context_degraded_step(
                reason=degraded_reason,
                transport_error=str(error),
                auth_state="denied",
            )
        )
        return _finalize_research_external_context_result(
            answer=_append_answer_note(
                internal_result.answer,
                "这次没有使用远程 MCP 上下文，因为当前凭据被目标端点拒绝。",
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
            mcp_server_id=AI_FRONTIER_EXTERNAL_MCP_SERVER_ID,
            mcp_resource_id=AI_FRONTIER_DIGEST_RESOURCE_ID,
            mcp_resource_uri=AI_FRONTIER_DIGEST_RESOURCE_URI,
            mcp_resource_display_name=AI_FRONTIER_DIGEST_RESOURCE_DISPLAY_NAME,
            mcp_tool_name=AI_FRONTIER_SEARCH_TOOL_NAME,
            mcp_prompt_name=AI_FRONTIER_BRIEF_PROMPT_NAME,
            mcp_transport="stdio_process",
            mcp_read_status="auth_denied",
            mcp_transport_error=str(error),
            mcp_endpoint_source=endpoint_source,
            mcp_endpoint_display_name=endpoint_display_name,
            mcp_endpoint_auth_state="denied",
            mcp_endpoint_auth_detail=str(error),
            context_selection_mode="mcp_resource",
        )
    except (McpRemoteTransportError, McpValidationError) as error:
        degraded_reason = "external_context_unavailable"
        tool_steps.append(
            _summarize_external_context_degraded_step(
                reason=degraded_reason,
                transport_error=str(error),
                auth_state=endpoint_auth_state,
            )
        )
        return _finalize_research_external_context_result(
            answer=_append_answer_note(
                internal_result.answer,
                "这次远程 MCP 资源暂时不可用，所以答案只反映当前工作区资料。",
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
            mcp_server_id=AI_FRONTIER_EXTERNAL_MCP_SERVER_ID,
            mcp_resource_id=AI_FRONTIER_DIGEST_RESOURCE_ID,
            mcp_resource_uri=AI_FRONTIER_DIGEST_RESOURCE_URI,
            mcp_resource_display_name=AI_FRONTIER_DIGEST_RESOURCE_DISPLAY_NAME,
            mcp_tool_name=AI_FRONTIER_SEARCH_TOOL_NAME,
            mcp_prompt_name=AI_FRONTIER_BRIEF_PROMPT_NAME,
            mcp_transport="stdio_process",
            mcp_read_status="transport_unavailable",
            mcp_transport_error=str(error),
            mcp_endpoint_source=endpoint_source,
            mcp_endpoint_display_name=endpoint_display_name,
            mcp_endpoint_auth_state=endpoint_auth_state,
            mcp_endpoint_auth_detail=endpoint_auth_detail,
            context_selection_mode="mcp_resource",
        )

    digest_text = mcp_resource.text.strip()
    digest_source = _serialize_digest_source(
        resource_id=mcp_resource.resource.id,
        resource_title=mcp_resource.resource.display_name,
        text=digest_text,
    )
    external_matches = _convert_mcp_tool_items_to_matches(mcp_tool.structured_content)

    tool_steps.append(
        _summarize_mcp_resource_step(
            resource_display_name=mcp_resource.resource.display_name,
            resource_uri=mcp_resource.resource.uri,
        )
    )
    tool_steps.append(_summarize_mcp_prompt_step(topic=prompt_topic))
    tool_steps.append(_summarize_mcp_tool_step(search_query=search_query, match_count=len(external_matches)))

    if not digest_text and not external_matches:
        degraded_reason = "external_context_no_useful_matches"
        tool_steps.append(_summarize_external_context_degraded_step(reason=degraded_reason))
        return _finalize_research_external_context_result(
            answer=_append_answer_note(
                internal_result.answer,
                "这次远程 MCP 资源没有提供足够有用的补充内容，所以答案只反映当前工作区资料。",
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
            mcp_server_id=mcp_resource.server.id,
            mcp_resource_id=mcp_resource.resource.id,
            mcp_resource_uri=mcp_resource.resource.uri,
            mcp_resource_display_name=mcp_resource.resource.display_name,
            mcp_tool_name=AI_FRONTIER_SEARCH_TOOL_NAME,
            mcp_prompt_name=AI_FRONTIER_BRIEF_PROMPT_NAME,
            mcp_transport=mcp_resource.server.transport,
            mcp_read_status="no_useful_matches",
            mcp_endpoint_source=endpoint_source,
            mcp_endpoint_display_name=endpoint_display_name,
            mcp_endpoint_auth_state=endpoint_auth_state,
            mcp_endpoint_auth_detail=endpoint_auth_detail,
            context_selection_mode="mcp_resource",
        )

    answer, prompt, synthesis_input_tokens, synthesis_output_tokens = _synthesize_external_context_answer(
        question=question,
        internal_result=internal_result,
        digest_text=digest_text or "没有额外摘要文本。",
        brief_prompt=mcp_prompt.text,
        external_matches=external_matches,
    )
    external_sources = _serialize_external_sources(external_matches)
    if digest_source is not None:
        external_sources = [digest_source, *external_sources]

    return _finalize_research_external_context_result(
        answer=answer,
        prompt=prompt,
        sources=[*internal_result.sources, *external_sources],
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
        mcp_server_id=mcp_resource.server.id,
        mcp_resource_id=mcp_resource.resource.id,
        mcp_resource_uri=mcp_resource.resource.uri,
        mcp_resource_display_name=mcp_resource.resource.display_name,
        mcp_tool_name=AI_FRONTIER_SEARCH_TOOL_NAME,
        mcp_prompt_name=AI_FRONTIER_BRIEF_PROMPT_NAME,
        mcp_transport=mcp_resource.server.transport,
        mcp_read_status="used",
        mcp_endpoint_source=endpoint_source,
        mcp_endpoint_display_name=endpoint_display_name,
        mcp_endpoint_auth_state=endpoint_auth_state,
        mcp_endpoint_auth_detail=endpoint_auth_detail,
        context_selection_mode="mcp_resource",
        tool_structured_content=mcp_tool.structured_content,
    )
