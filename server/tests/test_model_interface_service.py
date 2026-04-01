import pytest

from app.services.model_interface_service import (
    ModelInterfaceError,
    ModelMessage,
    ModelToolDefinition,
    OpenAICompatibleModelInterface,
    OpenAICompatibleModelSettings,
    resolve_api_key,
)


class FakeHTTPResponse:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self.payload


def test_generate_text_extracts_usage_and_tool_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_post(*args: object, **kwargs: object) -> FakeHTTPResponse:
        captured["url"] = kwargs.get("url", args[0] if args else None)
        captured["json"] = kwargs["json"]
        return FakeHTTPResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": "analysis text",
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "function": {
                                        "name": "search_workspace",
                                        "arguments": "{\"query\":\"apollo\"}",
                                    },
                                }
                            ],
                        },
                        "finish_reason": "tool_calls",
                    }
                ],
                "usage": {
                    "prompt_tokens": 13,
                    "completion_tokens": 7,
                    "total_tokens": 20,
                },
            }
        )

    monkeypatch.setattr("app.services.model_interface_service.httpx.post", fake_post)

    interface = OpenAICompatibleModelInterface(
        settings=OpenAICompatibleModelSettings(
            api_key="test-key",
            model="qwen-plus",
            base_url="https://example.com/v1",
            provider_name="qwen",
        )
    )
    response = interface.generate_text(
        messages=[ModelMessage(role="user", content="Analyze this.")],
        tools=[
            ModelToolDefinition(
                name="search_workspace",
                description="Search workspace context",
                input_json_schema={"type": "object"},
            )
        ],
    )

    assert captured["url"] == "https://example.com/v1/chat/completions"
    assert response.text == "analysis text"
    assert response.usage.input_tokens == 13
    assert response.usage.output_tokens == 7
    assert response.finish_reason == "tool_calls"
    assert response.tool_calls[0].name == "search_workspace"
    assert response.tool_calls[0].arguments_json == "{\"query\":\"apollo\"}"


def test_generate_json_object_uses_json_response_format(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_payload: dict[str, object] = {}

    def fake_post(*args: object, **kwargs: object) -> FakeHTTPResponse:
        captured_payload["payload"] = kwargs["json"]
        return FakeHTTPResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": "{\"score\": 0.8, \"reasoning\": \"Grounded.\"}"
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 9, "completion_tokens": 6, "total_tokens": 15},
            }
        )

    monkeypatch.setattr("app.services.model_interface_service.httpx.post", fake_post)

    interface = OpenAICompatibleModelInterface(
        settings=OpenAICompatibleModelSettings(
            api_key="judge-key",
            model="qwen-plus",
            base_url="https://example.com/v1",
            provider_name="qwen",
        )
    )
    response = interface.generate_json_object(
        messages=[ModelMessage(role="user", content="Judge this output.")],
    )

    assert captured_payload["payload"]["response_format"] == {"type": "json_object"}
    assert response.data == {"score": 0.8, "reasoning": "Grounded."}
    assert response.usage.total_tokens == 15


def test_embed_texts_orders_vectors_by_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(*args: object, **kwargs: object) -> FakeHTTPResponse:
        assert kwargs["json"]["input"] == ["first", "second"]
        return FakeHTTPResponse(
            {
                "data": [
                    {"index": 1, "embedding": [2.0, 3.0]},
                    {"index": 0, "embedding": [0.0, 1.0]},
                ]
            }
        )

    monkeypatch.setattr("app.services.model_interface_service.httpx.post", fake_post)

    interface = OpenAICompatibleModelInterface(
        settings=OpenAICompatibleModelSettings(
            api_key="embed-key",
            model="text-embedding-v4",
            base_url="https://example.com/v1",
            provider_name="qwen",
        )
    )
    response = interface.embed_texts(texts=["first", "second"])

    assert response.vectors == [[0.0, 1.0], [2.0, 3.0]]


def test_generate_text_requires_api_key() -> None:
    interface = OpenAICompatibleModelInterface(
        settings=OpenAICompatibleModelSettings(
            api_key="replace_me",
            model="qwen-plus",
            base_url="https://example.com/v1",
            provider_name="qwen",
        )
    )

    with pytest.raises(ModelInterfaceError, match="API key must be configured"):
        interface.generate_text(messages=[ModelMessage(role="user", content="hello")])


def test_resolve_api_key_uses_openai_fallback() -> None:
    assert (
        resolve_api_key(
            provider_name="openai",
            configured_api_key="replace_me",
            openai_api_key="real-openai-key",
        )
        == "real-openai-key"
    )
    assert (
        resolve_api_key(
            provider_name="qwen",
            configured_api_key="replace_me",
            openai_api_key="real-openai-key",
        )
        == "replace_me"
    )
