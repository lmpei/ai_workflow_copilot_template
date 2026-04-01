from dataclasses import dataclass

import pytest

from app.schemas.chat import ChatToolStep
from app.services import research_tool_assisted_chat_service
from app.services.model_interface_service import ModelJsonResponse, ModelTextResponse, ModelUsage
from app.services.research_tool_assisted_chat_service import run_tool_assisted_research_chat


@dataclass
class FakeModelInterface:
    planning_payload: dict[str, object]
    final_text: str
    json_calls: list[dict[str, object]]
    text_calls: list[dict[str, object]]

    def generate_json_object(self, **kwargs):
        self.json_calls.append(kwargs)
        return ModelJsonResponse(
            data=self.planning_payload,
            text=str(self.planning_payload),
            usage=ModelUsage(input_tokens=9, output_tokens=5, total_tokens=14),
        )

    def generate_text(self, **kwargs):
        self.text_calls.append(kwargs)
        return ModelTextResponse(
            text=self.final_text,
            usage=ModelUsage(input_tokens=21, output_tokens=13, total_tokens=34),
        )


def test_tool_assisted_chat_plans_search_executes_tools_and_returns_sources(monkeypatch) -> None:
    fake_interface = FakeModelInterface(
        planning_payload={
            'analysis_focus': 'Judge the most important market signal',
            'search_query': 'market signal competitor change',
        },
        final_text='This is the tool-assisted research conclusion.',
        json_calls=[],
        text_calls=[],
    )
    tool_calls: list[tuple[str, dict[str, object]]] = []

    def fake_invoke_inline_tool(*, workspace_id: str, user_id: str, tool_name: str, tool_input: dict[str, object]):
        tool_calls.append((tool_name, tool_input))
        if tool_name == 'list_workspace_documents':
            return {
                'documents': [
                    {
                        'id': 'doc-1',
                        'title': 'market-notes.txt',
                        'status': 'indexed',
                        'source_type': 'upload',
                        'mime_type': 'text/plain',
                    }
                ]
            }
        if tool_name == 'search_documents':
            return {
                'matches': [
                    {
                        'document_id': 'doc-1',
                        'chunk_id': 'chunk-1',
                        'document_title': 'market-notes.txt',
                        'chunk_index': 0,
                        'snippet': 'A competitor is rapidly adjusting its pricing strategy.',
                    }
                ]
            }
        raise AssertionError(f'unexpected tool {tool_name}')

    monkeypatch.setattr(research_tool_assisted_chat_service, '_invoke_inline_tool', fake_invoke_inline_tool)
    monkeypatch.setattr(research_tool_assisted_chat_service, 'get_chat_model_interface', lambda: fake_interface)

    result = run_tool_assisted_research_chat(
        workspace_id='workspace-1',
        user_id='user-1',
        question='What is the most important market signal right now?',
    )

    assert result.answer == 'This is the tool-assisted research conclusion.'
    assert result.analysis_focus == 'Judge the most important market signal'
    assert result.search_query == 'market signal competitor change'
    assert [step.tool_name for step in result.tool_steps] == [
        'list_workspace_documents',
        'search_documents',
    ]
    assert result.sources[0].chunk_id == 'chunk-1'
    assert result.token_input == 21
    assert result.token_output == 13
    assert result.degraded_reason is None
    assert tool_calls == [
        ('list_workspace_documents', {'limit': 20}),
        ('search_documents', {'query': 'market signal competitor change', 'limit': 4}),
    ]
    assert len(fake_interface.json_calls) == 1
    assert len(fake_interface.text_calls) == 1


def test_tool_assisted_chat_returns_guidance_when_no_documents(monkeypatch) -> None:
    def fake_invoke_inline_tool(*, workspace_id: str, user_id: str, tool_name: str, tool_input: dict[str, object]):
        assert tool_name == 'list_workspace_documents'
        return {'documents': []}

    monkeypatch.setattr(research_tool_assisted_chat_service, '_invoke_inline_tool', fake_invoke_inline_tool)
    monkeypatch.setattr(
        research_tool_assisted_chat_service,
        'get_chat_model_interface',
        lambda: pytest.fail('model interface should not be used without documents'),
    )

    result = run_tool_assisted_research_chat(
        workspace_id='workspace-1',
        user_id='user-1',
        question='Please analyze the current material.',
    )

    assert '可分析的资料' in result.answer
    assert result.sources == []
    assert result.tool_steps == [
        ChatToolStep(
            tool_name='list_workspace_documents',
            summary='没有发现可分析的资料。',
            detail='当前工作区还没有已接入并可用于研究的资料。',
        )
    ]
    assert result.token_input == 0
    assert result.token_output == 0
    assert result.degraded_reason == 'no_documents'
