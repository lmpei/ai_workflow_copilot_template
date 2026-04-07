import json
import sys
from typing import Any

from app.mcp.research_context_local_server import (
    ResearchContextLocalMcpServerError,
    build_research_context_local_mcp_server,
)
from app.schemas.mcp import (
    RESEARCH_CONTEXT_STDIO_MCP_SERVER_DISPLAY_NAME,
    RESEARCH_CONTEXT_STDIO_MCP_SERVER_ID,
    McpServerDefinition,
)

_SERVER = build_research_context_local_mcp_server()
_STDIO_SERVER = McpServerDefinition(
    id=RESEARCH_CONTEXT_STDIO_MCP_SERVER_ID,
    display_name=RESEARCH_CONTEXT_STDIO_MCP_SERVER_DISPLAY_NAME,
    summary="通过一个独立的本地子进程暴露同一份有边界的 Research MCP 资源，用来验证真实进程外读取路径。",
    transport="stdio_process",
    module_types=["research"],
    resource_ids=[resource.id for resource in _SERVER.resources],
)


def _success_response(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result,
    }


def _error_response(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": code,
            "message": message,
        },
    }


def _handle_request(payload: dict[str, Any]) -> dict[str, Any]:
    request_id = payload.get("id")
    method = payload.get("method")
    params = payload.get("params") if isinstance(payload.get("params"), dict) else {}

    if payload.get("jsonrpc") != "2.0":
        return _error_response(request_id, -32600, "Only JSON-RPC 2.0 requests are supported.")

    if method == "initialize":
        return _success_response(
            request_id,
            {
                "server": _STDIO_SERVER.model_dump(),
                "resources": [resource.model_dump() for resource in _SERVER.resources],
            },
        )

    if method == "resources/list":
        return _success_response(
            request_id,
            {
                "resources": [resource.model_dump() for resource in _SERVER.resources],
            },
        )

    if method == "resources/read":
        resource_id = params.get("resource_id")
        query = params.get("query")
        limit = params.get("limit", 3)
        if not isinstance(resource_id, str) or not resource_id:
            return _error_response(request_id, -32602, "resource_id must be a non-empty string.")
        if not isinstance(query, str) or not query.strip():
            return _error_response(request_id, -32602, "query must be a non-empty string.")
        if not isinstance(limit, int) or limit <= 0:
            return _error_response(request_id, -32602, "limit must be a positive integer.")
        try:
            result = _SERVER.read_resource(
                resource_id=resource_id,
                query=query,
                limit=limit,
            )
        except ResearchContextLocalMcpServerError as error:
            return _error_response(request_id, -32000, str(error))
        return _success_response(
            request_id,
            {
                "server": _STDIO_SERVER.model_dump(),
                "resource": result.resource.model_dump(),
                "text": result.text,
                "resource_count": result.resource_count,
                "items": [
                    {
                        "resource_id": item.resource_id,
                        "title": item.title,
                        "source_label": item.source_label,
                        "snippet": item.snippet,
                    }
                    for item in result.items
                ],
            },
        )

    if method == "ping":
        return _success_response(request_id, {"ok": True})

    return _error_response(request_id, -32601, f"Unsupported MCP method: {method}")


def main() -> int:
    for raw_line in sys.stdin:
        message = raw_line.strip()
        if not message:
            continue
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            response = _error_response(None, -32700, "Invalid JSON payload.")
        else:
            response = _handle_request(payload)
        sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
