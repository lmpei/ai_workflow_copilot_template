from dataclasses import dataclass, field

from app.connectors.research_external_context_connector import (
    ResearchExternalContextConnectorUnavailableError,
    ResearchExternalContextEntry,
    search_research_external_context,
)
from app.schemas.chat import ChatToolStep, SourceReference
from app.services.connector_service import (
    RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
    ConnectorConsentRequiredError,
    require_workspace_connector_consent,
)
from app.services.model_interface_service import ModelInterfaceError, ModelMessage
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


def _summarize_external_context_step(
    *,
    matches: list[ResearchExternalContextEntry],
    search_query: str,
) -> ChatToolStep:
    top_titles = "、".join(match.title for match in matches[:2])
    return ChatToolStep(
        tool_name="research_external_context",
        summary=f"已为“{search_query}”命中 {len(matches)} 条已授权外部信息。",
        detail=f"最明显的外部信息来源：{top_titles}" if top_titles else None,
    )


def _summarize_external_context_degraded_step(*, reason: str) -> ChatToolStep:
    if reason == "connector_consent_required":
        return ChatToolStep(
            tool_name="research_external_context",
            summary="这次没有使用外部信息，因为当前工作区还没有完成连接器授权。",
            detail="先授权工作区，再运行外部信息试点。",
        )
    if reason == "external_context_unavailable":
        return ChatToolStep(
            tool_name="research_external_context",
            summary="这次外部信息已获授权，但当前暂时不可用。",
            detail="系统已退回到只使用工作区资料的路径。",
        )
    return ChatToolStep(
        tool_name="research_external_context",
        summary="这次外部信息试点没有找到足够有用的补充信息。",
        detail="系统已退回到只使用工作区资料的路径。",
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
                        "You are running a bounded Research external-context pilot. "
                        "Use the provided workspace material and the approved external context only. "
                        "Keep the two evidence classes visibly distinct and do not invent extra sources."
                    ),
                ),
                ModelMessage(role="user", content=prompt),
            ],
        )
    except ModelInterfaceError as error:
        raise ChatProcessingError("Failed to generate the external-context research answer") from error

    answer = response.text.strip()
    if not answer:
        raise ChatProcessingError("External-context research analysis returned an empty answer")
    return answer, prompt, response.usage.input_tokens, response.usage.output_tokens


def run_research_external_context_chat(
    *,
    workspace_id: str,
    user_id: str,
    question: str,
    prior_memory: ResearchRunMemoryContext | None = None,
) -> ResearchExternalContextChatResult:
    internal_result = run_tool_assisted_research_chat(
        workspace_id=workspace_id,
        user_id=user_id,
        question=question,
        prior_memory=prior_memory,
    )

    tool_steps = list(internal_result.tool_steps)
    search_query = internal_result.search_query or question.strip()
    try:
        require_workspace_connector_consent(
            workspace_id=workspace_id,
            user_id=user_id,
            connector_id=RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
        )
    except ConnectorConsentRequiredError:
        degraded_reason = "connector_consent_required"
        tool_steps.append(_summarize_external_context_degraded_step(reason=degraded_reason))
        return ResearchExternalContextChatResult(
            answer=_append_answer_note(
                internal_result.answer,
                "这次没有使用外部信息，因为当前工作区还没有为这个试点完成授权。",
            ),
            prompt=internal_result.prompt,
            sources=internal_result.sources,
            tool_steps=tool_steps,
            token_input=internal_result.token_input,
            token_output=internal_result.token_output,
            analysis_focus=internal_result.analysis_focus,
            search_query=search_query,
            degraded_reason=degraded_reason,
            connector_consent_state="not_granted",
            external_context_used=False,
            external_match_count=0,
            external_matches=[],
        )

    try:
        external_matches = search_research_external_context(query=search_query, limit=_MAX_EXTERNAL_MATCHES)
    except ResearchExternalContextConnectorUnavailableError:
        degraded_reason = "external_context_unavailable"
        tool_steps.append(_summarize_external_context_degraded_step(reason=degraded_reason))
        return ResearchExternalContextChatResult(
            answer=_append_answer_note(
                internal_result.answer,
                "这次已获授权的外部信息暂时不可用，所以答案只反映当前工作区资料。",
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
        )

    if not external_matches:
        degraded_reason = "external_context_no_useful_matches"
        tool_steps.append(_summarize_external_context_degraded_step(reason=degraded_reason))
        return ResearchExternalContextChatResult(
            answer=_append_answer_note(
                internal_result.answer,
                "这次已授权的外部信息没有找到足够有用的补充内容。",
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
        )

    tool_steps.append(_summarize_external_context_step(matches=external_matches, search_query=search_query))
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
    )
