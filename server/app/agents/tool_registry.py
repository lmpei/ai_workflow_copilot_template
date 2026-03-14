from dataclasses import dataclass
from time import perf_counter
from typing import Callable

from pydantic import BaseModel, ValidationError

from app.repositories import document_repository, task_repository, workspace_repository
from app.schemas.document import DocumentResponse
from app.schemas.tool import (
    GetDocumentToolInput,
    GetDocumentToolOutput,
    ListWorkspaceDocumentsToolOutput,
    SearchDocumentMatch,
    SearchDocumentsToolInput,
    SearchDocumentsToolOutput,
    ToolDocumentSummary,
    WorkspaceDocumentsToolInput,
)
from app.services.retrieval_service import get_retriever


class ToolRegistryError(Exception):
    def __init__(self, message: str, *, tool_call_id: str | None = None) -> None:
        super().__init__(message)
        self.tool_call_id = tool_call_id


class UnknownToolError(ToolRegistryError):
    pass


class ToolAccessError(ToolRegistryError):
    pass


class ToolExecutionError(ToolRegistryError):
    pass


ToolHandler = Callable[[str, str, BaseModel], BaseModel]


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    name: str
    description: str
    input_model: type[BaseModel]
    handler: ToolHandler


@dataclass(frozen=True, slots=True)
class ToolInvocationResult:
    tool_call_id: str
    output: dict[str, object]


def _require_workspace_access(*, workspace_id: str, user_id: str) -> None:
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise ToolAccessError("Workspace not found")


def _to_document_summary(document: DocumentResponse) -> ToolDocumentSummary:
    return ToolDocumentSummary(
        id=document.id,
        title=document.title,
        status=document.status,
        source_type=document.source_type,
        mime_type=document.mime_type,
    )


def _search_documents_handler(
    workspace_id: str,
    user_id: str,
    tool_input: BaseModel,
) -> BaseModel:
    _require_workspace_access(workspace_id=workspace_id, user_id=user_id)
    search_input = SearchDocumentsToolInput.model_validate(tool_input.model_dump())
    retrieved_chunks = get_retriever().retrieve(
        workspace_id=workspace_id,
        question=search_input.query,
    )
    matches = [
        SearchDocumentMatch(
            document_id=chunk.document_id,
            chunk_id=chunk.chunk_id,
            document_title=chunk.document_title,
            chunk_index=chunk.chunk_index,
            snippet=chunk.snippet,
        )
        for chunk in retrieved_chunks[: search_input.limit]
    ]
    return SearchDocumentsToolOutput(matches=matches)


def _get_document_handler(
    workspace_id: str,
    user_id: str,
    tool_input: BaseModel,
) -> BaseModel:
    _require_workspace_access(workspace_id=workspace_id, user_id=user_id)
    document_input = GetDocumentToolInput.model_validate(tool_input.model_dump())
    document = document_repository.get_document(document_input.document_id, user_id)
    if document is None or document.workspace_id != workspace_id:
        raise ToolAccessError("Document not found")
    document_summary = _to_document_summary(DocumentResponse.from_model(document))
    return GetDocumentToolOutput(document=document_summary)


def _list_workspace_documents_handler(
    workspace_id: str,
    user_id: str,
    tool_input: BaseModel,
) -> BaseModel:
    _require_workspace_access(workspace_id=workspace_id, user_id=user_id)
    list_input = WorkspaceDocumentsToolInput.model_validate(tool_input.model_dump())
    documents = document_repository.list_documents(workspace_id=workspace_id, user_id=user_id)
    summaries = [
        _to_document_summary(DocumentResponse.from_model(document))
        for document in documents[: list_input.limit]
    ]
    return ListWorkspaceDocumentsToolOutput(documents=summaries)


TOOL_REGISTRY: dict[str, ToolDefinition] = {
    "search_documents": ToolDefinition(
        name="search_documents",
        description="Search indexed workspace documents by semantic similarity.",
        input_model=SearchDocumentsToolInput,
        handler=_search_documents_handler,
    ),
    "get_document": ToolDefinition(
        name="get_document",
        description="Fetch metadata for a single workspace document.",
        input_model=GetDocumentToolInput,
        handler=_get_document_handler,
    ),
    "list_workspace_documents": ToolDefinition(
        name="list_workspace_documents",
        description="List workspace documents and their ingest status.",
        input_model=WorkspaceDocumentsToolInput,
        handler=_list_workspace_documents_handler,
    ),
}


def list_tool_definitions() -> list[ToolDefinition]:
    return list(TOOL_REGISTRY.values())


def get_tool_definition(tool_name: str) -> ToolDefinition:
    definition = TOOL_REGISTRY.get(tool_name)
    if definition is None:
        raise UnknownToolError(f"Unknown tool: {tool_name}")
    return definition


def invoke_tool(
    *,
    agent_run_id: str,
    workspace_id: str,
    user_id: str,
    tool_name: str,
    tool_input: dict[str, object] | None = None,
) -> ToolInvocationResult:
    recorded_input = tool_input or {}
    tool_call = task_repository.create_tool_call(
        agent_run_id=agent_run_id,
        tool_name=tool_name,
        tool_input_json=recorded_input,
    )
    started_at = perf_counter()

    try:
        definition = get_tool_definition(tool_name)
        validated_input = definition.input_model.model_validate(recorded_input)
        running_call = task_repository.update_tool_call_status(
            tool_call.id,
            next_status="running",
        )
        if running_call is None:
            raise ToolExecutionError("Tool call not found", tool_call_id=tool_call.id)

        output_model = definition.handler(workspace_id, user_id, validated_input)
        output_payload = output_model.model_dump()
        completed_call = task_repository.update_tool_call_status(
            tool_call.id,
            next_status="completed",
            tool_output_json=output_payload,
            latency_ms=max(int((perf_counter() - started_at) * 1000), 0),
        )
        if completed_call is None:
            raise ToolExecutionError("Tool call not found", tool_call_id=tool_call.id)

        return ToolInvocationResult(tool_call_id=tool_call.id, output=output_payload)
    except ToolRegistryError as error:
        task_repository.update_tool_call_status(
            tool_call.id,
            next_status="failed",
            tool_output_json={"error": str(error)},
            latency_ms=max(int((perf_counter() - started_at) * 1000), 0),
        )
        error.tool_call_id = tool_call.id
        raise
    except ValidationError as error:
        task_repository.update_tool_call_status(
            tool_call.id,
            next_status="failed",
            tool_output_json={"error": str(error)},
            latency_ms=max(int((perf_counter() - started_at) * 1000), 0),
        )
        raise ToolExecutionError("Invalid tool input", tool_call_id=tool_call.id) from error
    except Exception as error:
        task_repository.update_tool_call_status(
            tool_call.id,
            next_status="failed",
            tool_output_json={"error": str(error)},
            latency_ms=max(int((perf_counter() - started_at) * 1000), 0),
        )
        raise ToolExecutionError(str(error), tool_call_id=tool_call.id) from error
