from dataclasses import dataclass

from app.schemas.chat import ChatToolStep, SourceReference
from app.schemas.tool import SearchDocumentMatch, ToolDocumentSummary
from app.services.model_interface_service import ModelInterfaceError, ModelMessage
from app.services.retrieval_generation_service import ChatProcessingError, get_chat_model_interface

_MAX_DOCUMENT_SUMMARY = 8
_MAX_MATCHES = 4


@dataclass(slots=True)
class ToolAssistedResearchChatResult:
    answer: str
    prompt: str
    sources: list[SourceReference]
    tool_steps: list[ChatToolStep]
    token_input: int
    token_output: int
    analysis_focus: str | None = None
    search_query: str | None = None
    degraded_reason: str | None = None


def _invoke_inline_tool(*, workspace_id: str, user_id: str, tool_name: str, tool_input: dict[str, object]) -> dict[str, object]:
    from app.agents.tool_registry import ToolRegistryError, invoke_tool_inline

    try:
        return invoke_tool_inline(
            workspace_id=workspace_id,
            user_id=user_id,
            tool_name=tool_name,
            tool_input=tool_input,
        )
    except ToolRegistryError as error:
        raise ChatProcessingError(str(error)) from error


def _parse_document_summaries(payload: dict[str, object]) -> list[ToolDocumentSummary]:
    raw_documents = payload.get('documents')
    if not isinstance(raw_documents, list):
        return []
    return [
        ToolDocumentSummary.model_validate(item)
        for item in raw_documents
        if isinstance(item, dict)
    ]


def _parse_matches(payload: dict[str, object]) -> list[SearchDocumentMatch]:
    raw_matches = payload.get('matches')
    if not isinstance(raw_matches, list):
        return []
    return [
        SearchDocumentMatch.model_validate(item)
        for item in raw_matches
        if isinstance(item, dict)
    ]


def _summarize_document_step(documents: list[ToolDocumentSummary]) -> ChatToolStep:
    if not documents:
        return ChatToolStep(
            tool_name='list_workspace_documents',
            summary='没有发现可分析的资料。',
            detail='当前工作区还没有已接入并可用于研究的资料。',
        )

    ready_count = sum(1 for document in documents if document.status == 'indexed')
    latest_titles = '、'.join(document.title for document in documents[:3])
    return ChatToolStep(
        tool_name='list_workspace_documents',
        summary=f'检查了 {len(documents)} 份资料，其中 {ready_count} 份可以直接用于分析。',
        detail=f'优先可见资料：{latest_titles}',
    )


def _build_document_inventory(documents: list[ToolDocumentSummary]) -> str:
    if not documents:
        return '当前工作区没有可用资料。'
    inventory_lines = [
        f'- {document.title} | status={document.status} | source={document.source_type}'
        for document in documents[:_MAX_DOCUMENT_SUMMARY]
    ]
    return '\n'.join(inventory_lines)


def _plan_search_query(*, question: str, documents: list[ToolDocumentSummary]) -> tuple[str, str]:
    model_interface = get_chat_model_interface()
    inventory = _build_document_inventory(documents)
    try:
        response = model_interface.generate_json_object(
            temperature=0.0,
            messages=[
                ModelMessage(
                    role='system',
                    content=(
                        'You are planning one bounded research-analysis pass. '
                        'Given a user question and a workspace document inventory, '
                        'return a JSON object with fields: analysis_focus, search_query. '
                        'search_query must be concise and optimized for semantic search. '
                        'Respond in the same language as the user question.'
                    ),
                ),
                ModelMessage(
                    role='user',
                    content=(
                        f'User question:\n{question}\n\n'
                        f'Workspace documents:\n{inventory}\n\n'
                        'Return JSON only.'
                    ),
                ),
            ],
        )
    except ModelInterfaceError as error:
        raise ChatProcessingError('Failed to plan the research search query') from error

    analysis_focus_raw = response.data.get('analysis_focus')
    search_query_raw = response.data.get('search_query')
    analysis_focus = analysis_focus_raw.strip() if isinstance(analysis_focus_raw, str) else ''
    search_query = search_query_raw.strip() if isinstance(search_query_raw, str) else ''

    if not search_query:
        search_query = question.strip()
    if not analysis_focus:
        analysis_focus = question.strip()

    return analysis_focus, search_query


def _summarize_search_step(*, search_query: str, matches: list[SearchDocumentMatch]) -> ChatToolStep:
    if not matches:
        return ChatToolStep(
            tool_name='search_documents',
            summary=f'围绕“{search_query}”没有找到足够强的命中片段。',
            detail='建议继续补充资料，或缩小问题范围后再试一次。',
        )

    top_titles = '、'.join(match.document_title for match in matches[:2])
    return ChatToolStep(
        tool_name='search_documents',
        summary=f'围绕“{search_query}”找到了 {len(matches)} 条相关片段。',
        detail=f'主要命中来自：{top_titles}',
    )


def _serialize_sources(matches: list[SearchDocumentMatch]) -> list[SourceReference]:
    return [
        SourceReference(
            document_id=match.document_id,
            chunk_id=match.chunk_id,
            document_title=match.document_title,
            chunk_index=match.chunk_index,
            snippet=match.snippet,
        )
        for match in matches
    ]


def _build_synthesis_prompt(
    *,
    question: str,
    analysis_focus: str,
    search_query: str,
    documents: list[ToolDocumentSummary],
    matches: list[SearchDocumentMatch],
) -> str:
    inventory = _build_document_inventory(documents)
    if matches:
        evidence_blocks = '\n\n'.join(
            (
                f'[{match.document_title} | chunk {match.chunk_index} | {match.chunk_id}]\n'
                f'{match.snippet}'
            )
            for match in matches
        )
    else:
        evidence_blocks = 'No grounded matches were found.'

    return (
        f'User question:\n{question}\n\n'
        f'Analysis focus:\n{analysis_focus}\n\n'
        f'Search query used:\n{search_query}\n\n'
        f'Workspace documents:\n{inventory}\n\n'
        f'Grounded evidence:\n{evidence_blocks}\n\n'
        'Answer in the same language as the user. '
        'Keep the response practical and structured. '
        'Explain: 1) the current conclusion, 2) what evidence supports it, 3) what is still missing or should happen next. '
        'If grounded evidence is weak, say that plainly.'
    )


def run_tool_assisted_research_chat(
    *,
    workspace_id: str,
    user_id: str,
    question: str,
) -> ToolAssistedResearchChatResult:
    documents_payload = _invoke_inline_tool(
        workspace_id=workspace_id,
        user_id=user_id,
        tool_name='list_workspace_documents',
        tool_input={'limit': 20},
    )
    documents = _parse_document_summaries(documents_payload)

    tool_steps: list[ChatToolStep] = [_summarize_document_step(documents)]
    if not documents:
        answer = '当前工作区还没有可分析的资料。请先上传并完成索引，然后再开始工具辅助分析。'
        return ToolAssistedResearchChatResult(
            answer=answer,
            prompt='no_documents',
            sources=[],
            tool_steps=tool_steps,
            token_input=0,
            token_output=0,
            degraded_reason='no_documents',
        )

    analysis_focus, search_query = _plan_search_query(question=question, documents=documents)
    matches_payload = _invoke_inline_tool(
        workspace_id=workspace_id,
        user_id=user_id,
        tool_name='search_documents',
        tool_input={'query': search_query, 'limit': _MAX_MATCHES},
    )
    matches = _parse_matches(matches_payload)

    tool_steps.append(_summarize_search_step(search_query=search_query, matches=matches))
    prompt = _build_synthesis_prompt(
        question=question,
        analysis_focus=analysis_focus,
        search_query=search_query,
        documents=documents,
        matches=matches,
    )
    try:
        response = get_chat_model_interface().generate_text(
            temperature=0.2,
            messages=[
                ModelMessage(
                    role='system',
                    content=(
                        'You are a research copilot running a bounded tool-assisted analysis pilot. '
                        'Use the supplied evidence and document inventory only. '
                        'Do not invent sources or certainty.'
                    ),
                ),
                ModelMessage(role='user', content=prompt),
            ],
        )
    except ModelInterfaceError as error:
        raise ChatProcessingError('Failed to generate the tool-assisted research answer') from error

    answer = response.text.strip()
    if not answer:
        raise ChatProcessingError('Tool-assisted research analysis returned an empty answer')

    return ToolAssistedResearchChatResult(
        answer=answer,
        prompt=prompt,
        sources=_serialize_sources(matches),
        tool_steps=tool_steps,
        token_input=response.usage.input_tokens,
        token_output=response.usage.output_tokens,
        analysis_focus=analysis_focus,
        search_query=search_query,
        degraded_reason='no_grounded_matches' if not matches else None,
    )
