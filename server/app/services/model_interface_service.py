import json
from dataclasses import dataclass, field
from typing import Any

import httpx


class ModelInterfaceError(Exception):
    pass


@dataclass(slots=True)
class ModelMessage:
    role: str
    content: str


@dataclass(slots=True)
class ModelToolDefinition:
    name: str
    description: str
    input_json_schema: dict[str, Any]


@dataclass(slots=True)
class ModelToolCall:
    id: str
    name: str
    arguments_json: str


@dataclass(slots=True)
class ModelUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


@dataclass(slots=True)
class ModelTextResponse:
    text: str
    usage: ModelUsage = field(default_factory=ModelUsage)
    finish_reason: str | None = None
    tool_calls: list[ModelToolCall] = field(default_factory=list)
    raw_json: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ModelJsonResponse:
    data: dict[str, Any]
    text: str
    usage: ModelUsage = field(default_factory=ModelUsage)
    finish_reason: str | None = None
    tool_calls: list[ModelToolCall] = field(default_factory=list)
    raw_json: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ModelEmbeddingResponse:
    vectors: list[list[float]]
    raw_json: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class OpenAICompatibleModelSettings:
    api_key: str
    model: str
    base_url: str
    provider_name: str


def resolve_api_key(
    *,
    provider_name: str,
    configured_api_key: str,
    openai_api_key: str,
) -> str:
    if configured_api_key == "replace_me" and provider_name == "openai":
        return openai_api_key
    return configured_api_key


@dataclass(slots=True)
class OpenAICompatibleModelInterface:
    settings: OpenAICompatibleModelSettings

    def generate_text(
        self,
        *,
        messages: list[ModelMessage],
        temperature: float = 0.0,
        response_format: dict[str, Any] | None = None,
        tools: list[ModelToolDefinition] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> ModelTextResponse:
        self._require_api_key()
        payload: dict[str, Any] = {
            "model": self.settings.model,
            "temperature": temperature,
            "messages": [
                {"role": message.role, "content": message.content}
                for message in messages
            ],
        }
        if response_format is not None:
            payload["response_format"] = response_format
        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_json_schema,
                    },
                }
                for tool in tools
            ]
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice

        try:
            raw_payload = self._post_json(
                path="/chat/completions",
                payload=payload,
                timeout=timeout,
            )
            return self._parse_text_response(raw_payload)
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
            raise ModelInterfaceError("Failed to generate model response") from error

    def generate_json_object(
        self,
        *,
        messages: list[ModelMessage],
        temperature: float = 0.0,
        timeout: float = 30.0,
    ) -> ModelJsonResponse:
        text_response = self.generate_text(
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
            timeout=timeout,
        )
        try:
            parsed = json.loads(text_response.text)
        except json.JSONDecodeError as error:
            raise ModelInterfaceError("Model did not return valid JSON") from error

        if not isinstance(parsed, dict):
            raise ModelInterfaceError("Model did not return a JSON object")

        return ModelJsonResponse(
            data=parsed,
            text=text_response.text,
            usage=text_response.usage,
            finish_reason=text_response.finish_reason,
            tool_calls=text_response.tool_calls,
            raw_json=text_response.raw_json,
        )

    def embed_texts(
        self,
        *,
        texts: list[str],
        timeout: float = 30.0,
    ) -> ModelEmbeddingResponse:
        if not texts:
            return ModelEmbeddingResponse(vectors=[])

        self._require_api_key()
        try:
            payload = self._post_json(
                path="/embeddings",
                payload={
                    "model": self.settings.model,
                    "input": texts,
                },
                timeout=timeout,
            )
            vectors = [
                item["embedding"]
                for item in sorted(payload["data"], key=lambda item: item["index"])
            ]
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
            raise ModelInterfaceError("Failed to generate embeddings") from error

        if len(vectors) != len(texts):
            raise ModelInterfaceError("Embedding response length did not match input count")

        return ModelEmbeddingResponse(vectors=vectors, raw_json=payload)

    def _require_api_key(self) -> None:
        if not self.settings.api_key or self.settings.api_key == "replace_me":
            raise ModelInterfaceError(
                f"{self.settings.provider_name} API key must be configured",
            )

    def _post_json(
        self,
        *,
        path: str,
        payload: dict[str, Any],
        timeout: float,
    ) -> dict[str, Any]:
        response = httpx.post(
            f"{self.settings.base_url}{path}",
            headers={
                "Authorization": f"Bearer {self.settings.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        raw_payload = response.json()
        if not isinstance(raw_payload, dict):
            raise TypeError("Model response payload must be a JSON object")
        return raw_payload

    def _parse_text_response(self, payload: dict[str, Any]) -> ModelTextResponse:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise KeyError("choices")

        choice = choices[0]
        if not isinstance(choice, dict):
            raise TypeError("choice")

        message = choice.get("message")
        if not isinstance(message, dict):
            raise KeyError("message")

        tool_calls = _extract_tool_calls(message)
        content = message.get("content")
        text = _extract_text_content(content)
        usage = _extract_usage(payload.get("usage"))
        finish_reason = choice.get("finish_reason")

        return ModelTextResponse(
            text=text,
            usage=usage,
            finish_reason=str(finish_reason) if finish_reason is not None else None,
            tool_calls=tool_calls,
            raw_json=payload,
        )


def _extract_text_content(content: object) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = [
            str(item.get("text", ""))
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        return "\n".join(part for part in text_parts if part)

    if content is None:
        return ""

    raise TypeError("Unsupported model content type")


def _extract_tool_calls(message: dict[str, Any]) -> list[ModelToolCall]:
    raw_tool_calls = message.get("tool_calls")
    if not isinstance(raw_tool_calls, list):
        return []

    parsed_tool_calls: list[ModelToolCall] = []
    for index, item in enumerate(raw_tool_calls):
        if not isinstance(item, dict):
            continue
        function_payload = item.get("function")
        if not isinstance(function_payload, dict):
            continue
        name = function_payload.get("name")
        arguments = function_payload.get("arguments")
        if not isinstance(name, str) or not isinstance(arguments, str):
            continue
        call_id = item.get("id")
        parsed_tool_calls.append(
            ModelToolCall(
                id=str(call_id) if call_id is not None else f"tool-call-{index}",
                name=name,
                arguments_json=arguments,
            )
        )
    return parsed_tool_calls


def _extract_usage(raw_usage: object) -> ModelUsage:
    if not isinstance(raw_usage, dict):
        return ModelUsage()
    return ModelUsage(
        input_tokens=int(raw_usage.get("prompt_tokens", 0)),
        output_tokens=int(raw_usage.get("completion_tokens", 0)),
        total_tokens=int(raw_usage.get("total_tokens", 0)),
    )
