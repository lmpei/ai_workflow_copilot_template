import json
import os
import subprocess
import sys
from typing import Any

from app.schemas.mcp import (
    McpResourceDefinition,
    McpResourceItem,
    McpResourceReadResult,
    McpServerDefinition,
    McpStdioServerConfig,
)


class McpProcessClientError(Exception):
    pass


def _build_command(config: McpStdioServerConfig) -> list[str]:
    if config.launch_kind != "python_module":
        raise McpProcessClientError(f"Unsupported MCP launch kind: {config.launch_kind}")
    return [sys.executable, "-m", config.module, *config.args]


def _run_exchange(
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
        timeout=5,
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


def _unwrap_result(response: dict[str, Any]) -> dict[str, Any]:
    if "error" in response:
        error_payload = response["error"]
        if isinstance(error_payload, dict):
            message = error_payload.get("message")
            if isinstance(message, str) and message:
                raise McpProcessClientError(message)
        raise McpProcessClientError("MCP process returned an unknown error.")
    result = response.get("result")
    if not isinstance(result, dict):
        raise McpProcessClientError("MCP process returned an invalid result payload.")
    return result


def describe_stdio_mcp_server(
    *,
    config: McpStdioServerConfig,
) -> tuple[McpServerDefinition, list[McpResourceDefinition]]:
    response = _run_exchange(
        config=config,
        requests=[
            {
                "jsonrpc": "2.0",
                "id": "initialize",
                "method": "initialize",
                "params": {},
            }
        ],
    )[0]
    result = _unwrap_result(response)
    server_payload = result.get("server")
    resources_payload = result.get("resources")
    if not isinstance(server_payload, dict):
        raise McpProcessClientError("MCP server metadata is missing.")
    if not isinstance(resources_payload, list):
        raise McpProcessClientError("MCP resource metadata is missing.")
    return (
        McpServerDefinition.model_validate(server_payload),
        [McpResourceDefinition.model_validate(resource) for resource in resources_payload],
    )


def read_stdio_mcp_resource(
    *,
    config: McpStdioServerConfig,
    resource_id: str,
    query: str,
    limit: int = 3,
) -> McpResourceReadResult:
    responses = _run_exchange(
        config=config,
        requests=[
            {
                "jsonrpc": "2.0",
                "id": "initialize",
                "method": "initialize",
                "params": {},
            },
            {
                "jsonrpc": "2.0",
                "id": "resource-read",
                "method": "resources/read",
                "params": {
                    "resource_id": resource_id,
                    "query": query,
                    "limit": limit,
                },
            },
        ],
    )
    _unwrap_result(responses[0])
    result = _unwrap_result(responses[1])
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
