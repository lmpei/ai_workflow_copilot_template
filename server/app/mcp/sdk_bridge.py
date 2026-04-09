from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


def _error(message: str, *, code: int = 1) -> int:
    sys.stderr.write(message + "\n")
    sys.stderr.flush()
    return code


def _read_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        raise ValueError("MCP SDK bridge expected one JSON payload on stdin.")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("MCP SDK bridge payload must be one JSON object.")
    return payload


def _build_server_params(payload: dict[str, Any]) -> StdioServerParameters:
    command = payload.get("command")
    cwd = payload.get("working_directory")
    if not isinstance(command, list) or not command or not all(isinstance(item, str) for item in command):
        raise ValueError("MCP SDK bridge requires a non-empty command list.")
    if not isinstance(cwd, str) or not cwd.strip():
        raise ValueError("MCP SDK bridge requires a working_directory.")

    env = payload.get("env_overrides")
    if env is None:
        env = {}
    if not isinstance(env, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in env.items()):
        raise ValueError("env_overrides must be a string-to-string object.")

    return StdioServerParameters(
        command=command[0],
        args=command[1:],
        cwd=cwd,
        env=env,
    )


async def _run(payload: dict[str, Any]) -> dict[str, Any]:
    operation = payload.get("operation")
    if not isinstance(operation, str) or not operation:
        raise ValueError("MCP SDK bridge requires a non-empty operation.")

    params = _build_server_params(payload)
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            init = await session.initialize()
            server_info = init.serverInfo.model_dump(mode="json")
            instructions = init.instructions

            if operation == "describe":
                resources = await session.list_resources()
                tools = await session.list_tools()
                prompts = await session.list_prompts()
                return {
                    "server_info": server_info,
                    "instructions": instructions,
                    "resources": [resource.model_dump(mode="json") for resource in resources.resources],
                    "tools": [tool.model_dump(mode="json") for tool in tools.tools],
                    "prompts": [prompt.model_dump(mode="json") for prompt in prompts.prompts],
                }

            if operation == "read_resource":
                resource_uri = payload.get("resource_uri")
                if not isinstance(resource_uri, str) or not resource_uri:
                    raise ValueError("read_resource requires resource_uri.")
                result = await session.read_resource(resource_uri)
                return {
                    "server_info": server_info,
                    "instructions": instructions,
                    "contents": [content.model_dump(mode="json") for content in result.contents],
                }

            if operation == "call_tool":
                tool_name = payload.get("tool_name")
                arguments = payload.get("arguments")
                if not isinstance(tool_name, str) or not tool_name:
                    raise ValueError("call_tool requires tool_name.")
                if arguments is None:
                    arguments = {}
                if not isinstance(arguments, dict):
                    raise ValueError("call_tool arguments must be an object.")
                result = await session.call_tool(tool_name, arguments=arguments)
                return {
                    "server_info": server_info,
                    "instructions": instructions,
                    "is_error": result.isError,
                    "structured_content": result.structuredContent,
                    "content": [content.model_dump(mode="json") for content in result.content],
                }

            if operation == "get_prompt":
                prompt_name = payload.get("prompt_name")
                arguments = payload.get("arguments")
                if not isinstance(prompt_name, str) or not prompt_name:
                    raise ValueError("get_prompt requires prompt_name.")
                if arguments is None:
                    arguments = {}
                if not isinstance(arguments, dict):
                    raise ValueError("get_prompt arguments must be an object.")
                result = await session.get_prompt(prompt_name, arguments=arguments)
                return {
                    "server_info": server_info,
                    "instructions": instructions,
                    "description": result.description,
                    "messages": [message.model_dump(mode="json") for message in result.messages],
                }

            raise ValueError(f"Unsupported MCP SDK bridge operation: {operation}")


def main() -> int:
    try:
        payload = _read_payload()
        result = asyncio.run(_run(payload))
    except Exception as error:  # pragma: no cover - subprocess entrypoint
        return _error(str(error))

    sys.stdout.write(json.dumps(result, ensure_ascii=False))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
