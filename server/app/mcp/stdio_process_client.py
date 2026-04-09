import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from app.schemas.mcp import (
    AI_FRONTIER_BRIEF_PROMPT_DISPLAY_NAME,
    AI_FRONTIER_BRIEF_PROMPT_NAME,
    AI_FRONTIER_SEARCH_TOOL_DISPLAY_NAME,
    AI_FRONTIER_SEARCH_TOOL_NAME,
    McpPromptDefinition,
    McpPromptRenderResult,
    McpResourceDefinition,
    McpResourceReadResult,
    McpServerDefinition,
    McpStdioServerConfig,
    McpToolCallResult,
    McpToolDefinition,
)


class McpProcessClientError(Exception):
    def __init__(self, message: str, *, code: int | None = None) -> None:
        super().__init__(message)
        self.code = code


_BRIDGE_SCRIPT = Path(__file__).with_name("sdk_bridge.py")


def _build_command(config: McpStdioServerConfig) -> list[str]:
    if config.launch_kind == "python_module":
        if not config.module:
            raise McpProcessClientError("MCP python-module launch requires a module.")
        return [sys.executable, "-m", config.module, *config.args]
    if config.launch_kind == "command":
        if not config.command:
            raise McpProcessClientError("MCP command launch requires a command.")
        return list(config.command)
    raise McpProcessClientError(f"Unsupported MCP launch kind: {config.launch_kind}")


def _use_sdk_bridge(config: McpStdioServerConfig) -> bool:
    return config.launch_kind == "command" and any("weave_mcp_server" in part for part in config.command)


def _run_legacy_exchange(
    *,
    config: McpStdioServerConfig,
    requests: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    command = _build_command(config)
    payload = "".join(f"{json.dumps(request, ensure_ascii=False)}\n" for request in requests)
    env = os.environ.copy()
    env.update(config.env_overrides)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    completed = subprocess.run(
        command,
        input=payload,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=config.working_directory,
        env=env,
        timeout=8,
        check=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or "Unknown MCP process failure."
        raise McpProcessClientError(stderr)
    stdout_lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if len(stdout_lines) != len(requests):
        raise McpProcessClientError("Unexpected MCP process response count.")
    responses: list[dict[str, Any]] = []
    for line in stdout_lines:
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError as error:
            raise McpProcessClientError("Invalid JSON returned by MCP process.") from error
        if not isinstance(parsed, dict):
            raise McpProcessClientError("Unexpected MCP response payload shape.")
        responses.append(parsed)
    return responses


def _run_sdk_bridge(
    *,
    config: McpStdioServerConfig,
    payload: dict[str, Any],
) -> dict[str, Any]:
    if not config.command:
        raise McpProcessClientError("MCP SDK bridge requires a command-based config.")

    bridge_python = config.command[0]
    bridge_payload = {
        "command": list(config.command),
        "working_directory": config.working_directory,
        "env_overrides": config.env_overrides,
        **payload,
    }
    completed = subprocess.run(
        [bridge_python, str(_BRIDGE_SCRIPT)],
        input=json.dumps(bridge_payload, ensure_ascii=False),
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=config.working_directory,
        timeout=12,
        check=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or "Unknown MCP SDK bridge failure."
        raise McpProcessClientError(stderr)
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise McpProcessClientError("Invalid JSON returned by MCP SDK bridge.") from error
    if not isinstance(result, dict):
        raise McpProcessClientError("Unexpected MCP SDK bridge payload shape.")
    return result


def _unwrap_legacy_result(response: dict[str, Any]) -> dict[str, Any]:
    if "error" in response:
        error_payload = response["error"]
        if isinstance(error_payload, dict):
            message = error_payload.get("message")
            code = error_payload.get("code")
            if isinstance(message, str) and message:
                raise McpProcessClientError(message, code=code if isinstance(code, int) else None)
        raise McpProcessClientError("MCP process returned an unknown error.")
    result = response.get("result")
    if not isinstance(result, dict):
        raise McpProcessClientError("MCP process returned an invalid result payload.")
    return result


def _with_auth_params(
    params: dict[str, Any],
    *,
    config: McpStdioServerConfig,
) -> dict[str, Any]:
    if config.auth_token:
        return {
            **params,
            "auth": {
                "token": config.auth_token,
            },
        }
    return params


def _parse_server(server_info: dict[str, Any], fallback_transport: str) -> McpServerDefinition:
    server_id = server_info.get("name") or server_info.get("id") or "unknown_mcp_server"
    display_name = server_info.get("title") or server_info.get("display_name") or server_id
    return McpServerDefinition(
        id=str(server_id),
        display_name=str(display_name),
        summary=str(server_info.get("description") or server_info.get("summary") or "MCP server"),
        transport=fallback_transport,
        module_types=["research"],
        resource_ids=[],
        tool_names=[],
        prompt_names=[],
    )


def _text_content_to_string(content_items: list[dict[str, Any]]) -> str | None:
    texts = [
        item.get("text")
        for item in content_items
        if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str)
    ]
    joined = "\n\n".join(text.strip() for text in texts if text and text.strip())
    return joined or None


def _prompt_messages_to_string(messages: list[dict[str, Any]]) -> str:
    texts: list[str] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if isinstance(content, dict) and content.get("type") == "text" and isinstance(content.get("text"), str):
            texts.append(content["text"].strip())
    return "\n\n".join(text for text in texts if text)


def describe_stdio_mcp_server(
    *,
    config: McpStdioServerConfig,
) -> tuple[McpServerDefinition, list[McpResourceDefinition], list[McpToolDefinition], list[McpPromptDefinition]]:
    if _use_sdk_bridge(config):
        result = _run_sdk_bridge(config=config, payload={"operation": "describe"})
        server = _parse_server(result.get("server_info", {}), config.transport)
        resources_payload = result.get("resources", [])
        tools_payload = result.get("tools", [])
        prompts_payload = result.get("prompts", [])
        resources = [
            McpResourceDefinition(
                id=resource.get("name", ""),
                uri=resource.get("uri", ""),
                display_name=resource.get("title") or resource.get("name") or resource.get("uri") or "",
                summary=resource.get("description") or "",
                mime_type=resource.get("mimeType") or "text/plain",
                module_types=["research"],
                connector_id="research_external_context",
            )
            for resource in resources_payload
            if isinstance(resource, dict)
        ]
        tools = [
            McpToolDefinition(
                name=tool.get("name", ""),
                display_name=tool.get("title") or tool.get("name") or "",
                summary=tool.get("description") or "",
                module_types=["research"],
                connector_id="research_external_context",
            )
            for tool in tools_payload
            if isinstance(tool, dict)
        ]
        prompts = [
            McpPromptDefinition(
                name=prompt.get("name", ""),
                display_name=prompt.get("title") or prompt.get("name") or "",
                summary=prompt.get("description") or "",
                module_types=["research"],
                connector_id="research_external_context",
            )
            for prompt in prompts_payload
            if isinstance(prompt, dict)
        ]
        server.resource_ids = [resource.id for resource in resources]
        server.tool_names = [tool.name for tool in tools]
        server.prompt_names = [prompt.name for prompt in prompts]
        return server, resources, tools, prompts

    response = _run_legacy_exchange(
        config=config,
        requests=[
            {
                "jsonrpc": "2.0",
                "id": "initialize",
                "method": "initialize",
                "params": _with_auth_params({}, config=config),
            }
        ],
    )[0]
    result = _unwrap_legacy_result(response)
    server_payload = result.get("server")
    resources_payload = result.get("resources")
    if not isinstance(server_payload, dict):
        raise McpProcessClientError("MCP server metadata is missing.")
    if not isinstance(resources_payload, list):
        raise McpProcessClientError("MCP resource metadata is missing.")
    server = McpServerDefinition.model_validate(server_payload)
    resources = [McpResourceDefinition.model_validate(resource) for resource in resources_payload]
    return server, resources, [], []


def read_stdio_mcp_resource(
    *,
    config: McpStdioServerConfig,
    resource_id: str,
    resource_uri: str,
    query: str,
    limit: int = 3,
) -> McpResourceReadResult:
    if _use_sdk_bridge(config):
        result = _run_sdk_bridge(
            config=config,
            payload={
                "operation": "read_resource",
                "resource_uri": resource_uri,
            },
        )
        server = _parse_server(result.get("server_info", {}), config.transport)
        text = _text_content_to_string(result.get("contents", [])) or ""
        resource = McpResourceDefinition(
            id=resource_id,
            uri=resource_uri,
            display_name=resource_id,
            summary=result.get("instructions") or "",
            mime_type="text/plain",
            module_types=["research"],
            connector_id="research_external_context",
        )
        server.resource_ids = [resource.id]
        return McpResourceReadResult(
            server=server,
            resource=resource,
            text=text,
            resource_count=1 if text else 0,
            items=(),
        )

    responses = _run_legacy_exchange(
        config=config,
        requests=[
            {
                "jsonrpc": "2.0",
                "id": "initialize",
                "method": "initialize",
                "params": _with_auth_params({}, config=config),
            },
            {
                "jsonrpc": "2.0",
                "id": "resource-read",
                "method": "resources/read",
                "params": _with_auth_params(
                    {
                        "resource_id": resource_id,
                        "query": query,
                        "limit": limit,
                    },
                    config=config,
                ),
            },
        ],
    )
    _unwrap_legacy_result(responses[0])
    result = _unwrap_legacy_result(responses[1])
    server_payload = result.get("server")
    resource_payload = result.get("resource")
    items_payload = result.get("items", [])
    resource_count = result.get("resource_count")
    text = result.get("text")
    if not isinstance(server_payload, dict):
        raise McpProcessClientError("MCP read result is missing server metadata.")
    if not isinstance(resource_payload, dict):
        raise McpProcessClientError("MCP read result is missing resource metadata.")
    if not isinstance(items_payload, list):
        raise McpProcessClientError("MCP read result items are invalid.")
    if not isinstance(resource_count, int):
        raise McpProcessClientError("MCP read result count is invalid.")
    if not isinstance(text, str):
        raise McpProcessClientError("MCP read result text is invalid.")
    from app.schemas.mcp import McpResourceItem

    items: list[McpResourceItem] = []
    for item in items_payload:
        if not isinstance(item, dict):
            raise McpProcessClientError("MCP resource item is invalid.")
        items.append(
            McpResourceItem(
                resource_id=str(item.get("resource_id", "")),
                title=str(item.get("title", "")),
                source_label=str(item.get("source_label", "")),
                snippet=str(item.get("snippet", "")),
            )
        )
    return McpResourceReadResult(
        server=McpServerDefinition.model_validate(server_payload),
        resource=McpResourceDefinition.model_validate(resource_payload),
        text=text,
        resource_count=resource_count,
        items=tuple(items),
    )


def call_stdio_mcp_tool(
    *,
    config: McpStdioServerConfig,
    tool_name: str,
    arguments: dict[str, Any],
) -> McpToolCallResult:
    if not _use_sdk_bridge(config):
        raise McpProcessClientError("Legacy MCP process does not expose MCP tools.")
    result = _run_sdk_bridge(
        config=config,
        payload={
            "operation": "call_tool",
            "tool_name": tool_name,
            "arguments": arguments,
        },
    )
    server = _parse_server(result.get("server_info", {}), config.transport)
    tool = McpToolDefinition(
        name=tool_name,
        display_name=AI_FRONTIER_SEARCH_TOOL_DISPLAY_NAME if tool_name == AI_FRONTIER_SEARCH_TOOL_NAME else tool_name,
        summary=result.get("instructions") or "MCP tool call",
        module_types=["research"],
        connector_id="research_external_context",
    )
    server.tool_names = [tool.name]
    return McpToolCallResult(
        server=server,
        tool=tool,
        structured_content=result.get("structured_content") if isinstance(result.get("structured_content"), dict) else None,
        text_content=_text_content_to_string(result.get("content", [])),
        is_error=bool(result.get("is_error")),
    )


def get_stdio_mcp_prompt(
    *,
    config: McpStdioServerConfig,
    prompt_name: str,
    arguments: dict[str, str],
) -> McpPromptRenderResult:
    if not _use_sdk_bridge(config):
        raise McpProcessClientError("Legacy MCP process does not expose MCP prompts.")
    result = _run_sdk_bridge(
        config=config,
        payload={
            "operation": "get_prompt",
            "prompt_name": prompt_name,
            "arguments": arguments,
        },
    )
    server = _parse_server(result.get("server_info", {}), config.transport)
    prompt = McpPromptDefinition(
        name=prompt_name,
        display_name=AI_FRONTIER_BRIEF_PROMPT_DISPLAY_NAME if prompt_name == AI_FRONTIER_BRIEF_PROMPT_NAME else prompt_name,
        summary=result.get("description") or "MCP prompt render",
        module_types=["research"],
        connector_id="research_external_context",
    )
    server.prompt_names = [prompt.name]
    return McpPromptRenderResult(
        server=server,
        prompt=prompt,
        description=result.get("description") if isinstance(result.get("description"), str) else None,
        text=_prompt_messages_to_string(result.get("messages", [])),
    )
