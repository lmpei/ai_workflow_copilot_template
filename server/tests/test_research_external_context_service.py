from dataclasses import dataclass

from app.schemas.chat import ChatToolStep, SourceReference
from app.schemas.mcp import (
    AI_FRONTIER_BRIEF_PROMPT_NAME,
    AI_FRONTIER_DIGEST_RESOURCE_DISPLAY_NAME,
    AI_FRONTIER_DIGEST_RESOURCE_ID,
    AI_FRONTIER_DIGEST_RESOURCE_URI,
    AI_FRONTIER_EXTERNAL_MCP_SERVER_ID,
    AI_FRONTIER_SEARCH_TOOL_NAME,
    McpPromptDefinition,
    McpPromptRenderResult,
    McpResourceDefinition,
    McpResourceReadResult,
    McpServerDefinition,
    McpToolCallResult,
    McpToolDefinition,
)
from app.schemas.research_external_resource_snapshot import ResearchExternalResourceSnapshotResponse
from app.services import research_external_context_service
from app.services.mcp_service import (
    McpExternalEndpointNotConfiguredError,
    McpRemoteAuthDeniedError,
    McpRemoteAuthRequiredError,
    McpValidationError,
)
from app.services.research_external_context_service import run_research_external_context_chat
from app.services.research_tool_assisted_chat_service import ToolAssistedResearchChatResult


@dataclass
class FakeModelInterface:
    text: str
    calls: list[dict[str, object]]

    def generate_text(self, **kwargs):
        self.calls.append(kwargs)
        from app.services.model_interface_service import ModelTextResponse, ModelUsage

        return ModelTextResponse(
            text=self.text,
            usage=ModelUsage(input_tokens=11, output_tokens=7, total_tokens=18),
        )


def _build_internal_result(*, degraded_reason: str | None = None) -> ToolAssistedResearchChatResult:
    return ToolAssistedResearchChatResult(
        answer="Internal workspace material points to pricing pressure.",
        prompt="internal prompt",
        sources=[
            SourceReference(
                document_id="doc-1",
                chunk_id="chunk-1",
                document_title="market-notes.txt",
                chunk_index=0,
                snippet="Workspace material points to pricing pressure.",
                source_kind="workspace_document",
            )
        ],
        tool_steps=[
            ChatToolStep(
                tool_name="search_documents",
                summary="Found grounded workspace material.",
            )
        ],
        token_input=10,
        token_output=8,
        analysis_focus="Judge the strongest market signal",
        search_query="pricing pressure market signal",
        degraded_reason=degraded_reason,
    )


def _build_mcp_read_result() -> McpResourceReadResult:
    return McpResourceReadResult(
        server=McpServerDefinition(
            id=AI_FRONTIER_EXTERNAL_MCP_SERVER_ID,
            display_name="AI 前沿研究外部 MCP 服务",
            summary="Bounded external MCP pilot",
            transport="stdio_process",
            module_types=["research"],
            resource_ids=[AI_FRONTIER_DIGEST_RESOURCE_ID],
            tool_names=[AI_FRONTIER_SEARCH_TOOL_NAME],
            prompt_names=[AI_FRONTIER_BRIEF_PROMPT_NAME],
        ),
        resource=McpResourceDefinition(
            id=AI_FRONTIER_DIGEST_RESOURCE_ID,
            uri=AI_FRONTIER_DIGEST_RESOURCE_URI,
            display_name=AI_FRONTIER_DIGEST_RESOURCE_DISPLAY_NAME,
            summary="Bounded MCP digest",
            mime_type="text/markdown",
            module_types=["research"],
            connector_id="research_external_context",
        ),
        text="## Analyst note\nSource: External market note\n\nExternal analysts also see sustained pricing pressure.",
        resource_count=1,
        items=(),
    )


def _build_mcp_prompt_result() -> McpPromptRenderResult:
    return McpPromptRenderResult(
        server=McpServerDefinition(
            id=AI_FRONTIER_EXTERNAL_MCP_SERVER_ID,
            display_name="AI 前沿研究外部 MCP 服务",
            summary="Bounded external MCP pilot",
            transport="stdio_process",
            module_types=["research"],
            resource_ids=[AI_FRONTIER_DIGEST_RESOURCE_ID],
            tool_names=[AI_FRONTIER_SEARCH_TOOL_NAME],
            prompt_names=[AI_FRONTIER_BRIEF_PROMPT_NAME],
        ),
        prompt=McpPromptDefinition(
            name=AI_FRONTIER_BRIEF_PROMPT_NAME,
            display_name="AI 前沿研究 Brief",
            summary="Bounded MCP brief",
            module_types=["research"],
            connector_id="research_external_context",
        ),
        description="Reusable AI frontier brief",
        text="请先总结，再判断，再列项目卡片。",
    )


def _build_mcp_tool_result() -> McpToolCallResult:
    return McpToolCallResult(
        server=McpServerDefinition(
            id=AI_FRONTIER_EXTERNAL_MCP_SERVER_ID,
            display_name="AI 前沿研究外部 MCP 服务",
            summary="Bounded external MCP pilot",
            transport="stdio_process",
            module_types=["research"],
            resource_ids=[AI_FRONTIER_DIGEST_RESOURCE_ID],
            tool_names=[AI_FRONTIER_SEARCH_TOOL_NAME],
            prompt_names=[AI_FRONTIER_BRIEF_PROMPT_NAME],
        ),
        tool=McpToolDefinition(
            name=AI_FRONTIER_SEARCH_TOOL_NAME,
            display_name="AI 前沿搜索",
            summary="Search bounded frontier items",
            module_types=["research"],
            connector_id="research_external_context",
        ),
        structured_content={
            "items": [
                {
                    "id": "project-1",
                    "title": "Agent framework update",
                    "source_label": "Official project release",
                    "summary": "The framework added deeper tool visibility.",
                    "why_it_matters": "This could affect engineering choices.",
                    "source_url": "https://example.com/project",
                    "repo_url": "https://github.com/example/project",
                    "docs_url": "https://docs.example.com/project",
                }
            ]
        },
        text_content="Matched one AI frontier project.",
        is_error=False,
    )


def _patch_endpoint_state(monkeypatch, *, auth_state: str = "not_required", auth_detail: str | None = None) -> None:
    monkeypatch.setattr(
        research_external_context_service,
        "describe_workspace_true_external_mcp_endpoint",
        lambda **_: (
            type(
                "Endpoint",
                (),
                {
                    "source": "external_configured",
                    "display_name": "AI 前沿研究外部 MCP 服务",
                },
            )(),
            auth_state,
            auth_detail,
        ),
    )


def test_external_context_chat_degrades_honestly_when_consent_is_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        research_external_context_service,
        "run_tool_assisted_research_chat",
        lambda **_: _build_internal_result(),
    )
    _patch_endpoint_state(monkeypatch)

    def require_consent(**kwargs):
        raise research_external_context_service.ConnectorConsentRequiredError(
            "consent required",
            consent_state="not_granted",
        )

    monkeypatch.setattr(research_external_context_service, "require_workspace_connector_consent", require_consent)

    result = run_research_external_context_chat(
        workspace_id="workspace-1",
        user_id="user-1",
        question="What is the strongest current signal?",
    )

    assert result.degraded_reason == "connector_consent_required"
    assert result.external_context_used is False
    assert result.connector_consent_state == "not_granted"
    assert result.context_selection_mode == "mcp_resource"
    assert result.mcp_server_id == AI_FRONTIER_EXTERNAL_MCP_SERVER_ID
    assert result.mcp_resource_id == AI_FRONTIER_DIGEST_RESOURCE_ID
    assert result.mcp_resource_uri == AI_FRONTIER_DIGEST_RESOURCE_URI
    assert result.mcp_resource_display_name == AI_FRONTIER_DIGEST_RESOURCE_DISPLAY_NAME
    assert result.mcp_tool_name == AI_FRONTIER_SEARCH_TOOL_NAME
    assert result.mcp_prompt_name == AI_FRONTIER_BRIEF_PROMPT_NAME
    assert result.mcp_transport == "stdio_process"
    assert result.mcp_read_status == "consent_required"
    assert result.mcp_transport_error is None
    assert result.mcp_endpoint_source == "external_configured"
    assert result.mcp_endpoint_auth_state == "not_required"


def test_external_context_chat_combines_internal_and_true_external_mcp_outputs(monkeypatch) -> None:
    monkeypatch.setattr(
        research_external_context_service,
        "run_tool_assisted_research_chat",
        lambda **_: _build_internal_result(),
    )
    monkeypatch.setattr(
        research_external_context_service,
        "require_workspace_connector_consent",
        lambda **_: object(),
    )
    monkeypatch.setattr(
        research_external_context_service,
        "read_workspace_true_external_mcp_resource",
        lambda **_: _build_mcp_read_result(),
    )
    monkeypatch.setattr(
        research_external_context_service,
        "get_workspace_true_external_mcp_prompt",
        lambda **_: _build_mcp_prompt_result(),
    )
    monkeypatch.setattr(
        research_external_context_service,
        "call_workspace_true_external_mcp_tool",
        lambda **_: _build_mcp_tool_result(),
    )
    _patch_endpoint_state(monkeypatch)
    fake_interface = FakeModelInterface(
        text="Workspace material shows pricing pressure, and the external MCP path confirms it is market-wide.",
        calls=[],
    )
    monkeypatch.setattr(research_external_context_service, "get_chat_model_interface", lambda: fake_interface)

    result = run_research_external_context_chat(
        workspace_id="workspace-1",
        user_id="user-1",
        question="What is the strongest current signal?",
    )

    assert result.degraded_reason is None
    assert result.external_context_used is True
    assert result.external_match_count == 1
    assert len(result.sources) == 3
    assert result.sources[0].source_kind == "workspace_document"
    assert result.sources[1].source_kind == "external_context"
    assert result.sources[2].source_kind == "external_context"
    assert len(fake_interface.calls) == 1
    assert [step.tool_name for step in result.tool_steps[-3:]] == ["mcp_resource", "mcp_prompt", "mcp_tool"]
    assert result.mcp_server_id == AI_FRONTIER_EXTERNAL_MCP_SERVER_ID
    assert result.mcp_resource_id == AI_FRONTIER_DIGEST_RESOURCE_ID
    assert result.mcp_resource_uri == AI_FRONTIER_DIGEST_RESOURCE_URI
    assert result.mcp_resource_display_name == AI_FRONTIER_DIGEST_RESOURCE_DISPLAY_NAME
    assert result.mcp_tool_name == AI_FRONTIER_SEARCH_TOOL_NAME
    assert result.mcp_prompt_name == AI_FRONTIER_BRIEF_PROMPT_NAME
    assert result.context_selection_mode == "mcp_resource"
    assert result.mcp_transport == "stdio_process"
    assert result.mcp_read_status == "used"
    assert result.mcp_transport_error is None
    assert result.mcp_endpoint_source == "external_configured"
    assert result.mcp_endpoint_auth_state == "not_required"


def test_external_context_chat_degrades_when_true_external_endpoint_is_not_configured(monkeypatch) -> None:
    monkeypatch.setattr(
        research_external_context_service,
        "run_tool_assisted_research_chat",
        lambda **_: _build_internal_result(),
    )
    monkeypatch.setattr(
        research_external_context_service,
        "require_workspace_connector_consent",
        lambda **_: object(),
    )
    monkeypatch.setattr(
        research_external_context_service,
        "describe_workspace_true_external_mcp_endpoint",
        lambda **_: (None, "not_required", None),
    )

    def unavailable(**kwargs):
        raise McpExternalEndpointNotConfiguredError("True external MCP endpoint is not configured for this connector")

    monkeypatch.setattr(research_external_context_service, "read_workspace_true_external_mcp_resource", unavailable)

    result = run_research_external_context_chat(
        workspace_id="workspace-1",
        user_id="user-1",
        question="What is the strongest current signal?",
    )

    assert result.degraded_reason == "external_context_unavailable"
    assert result.external_context_used is False
    assert result.context_selection_mode == "mcp_resource"
    assert result.mcp_server_id == AI_FRONTIER_EXTERNAL_MCP_SERVER_ID
    assert result.mcp_read_status == "transport_unavailable"
    assert "not configured" in (result.mcp_transport_error or "")
    assert result.mcp_endpoint_source is None


def test_external_context_chat_degrades_when_true_external_auth_is_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        research_external_context_service,
        "run_tool_assisted_research_chat",
        lambda **_: _build_internal_result(),
    )
    monkeypatch.setattr(
        research_external_context_service,
        "require_workspace_connector_consent",
        lambda **_: object(),
    )
    _patch_endpoint_state(
        monkeypatch,
        auth_state="missing",
        auth_detail="External MCP auth token is required but not configured.",
    )

    def auth_required(**kwargs):
        raise McpRemoteAuthRequiredError("MCP authentication is required.")

    monkeypatch.setattr(research_external_context_service, "read_workspace_true_external_mcp_resource", auth_required)

    result = run_research_external_context_chat(
        workspace_id="workspace-1",
        user_id="user-1",
        question="What is the strongest current signal?",
    )

    assert result.degraded_reason == "external_context_auth_required"
    assert result.mcp_read_status == "auth_required"
    assert result.mcp_endpoint_auth_state == "missing"
    assert "required" in (result.mcp_endpoint_auth_detail or "")


def test_external_context_chat_degrades_when_true_external_auth_is_denied(monkeypatch) -> None:
    monkeypatch.setattr(
        research_external_context_service,
        "run_tool_assisted_research_chat",
        lambda **_: _build_internal_result(),
    )
    monkeypatch.setattr(
        research_external_context_service,
        "require_workspace_connector_consent",
        lambda **_: object(),
    )
    _patch_endpoint_state(
        monkeypatch,
        auth_state="configured",
        auth_detail="External MCP auth token is configured for this connector.",
    )

    def auth_denied(**kwargs):
        raise McpRemoteAuthDeniedError("MCP authentication was denied.")

    monkeypatch.setattr(research_external_context_service, "read_workspace_true_external_mcp_resource", auth_denied)

    result = run_research_external_context_chat(
        workspace_id="workspace-1",
        user_id="user-1",
        question="What is the strongest current signal?",
    )

    assert result.degraded_reason == "external_context_auth_denied"
    assert result.mcp_read_status == "auth_denied"
    assert result.mcp_endpoint_auth_state == "denied"
    assert "denied" in (result.mcp_endpoint_auth_detail or "")


def test_external_context_chat_degrades_when_true_external_mcp_resource_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(
        research_external_context_service,
        "run_tool_assisted_research_chat",
        lambda **_: _build_internal_result(),
    )
    monkeypatch.setattr(
        research_external_context_service,
        "require_workspace_connector_consent",
        lambda **_: object(),
    )
    _patch_endpoint_state(monkeypatch)

    def unavailable(**kwargs):
        raise McpValidationError("down")

    monkeypatch.setattr(research_external_context_service, "read_workspace_true_external_mcp_resource", unavailable)

    result = run_research_external_context_chat(
        workspace_id="workspace-1",
        user_id="user-1",
        question="What is the strongest current signal?",
    )

    assert result.degraded_reason == "external_context_unavailable"
    assert result.external_context_used is False
    assert result.context_selection_mode == "mcp_resource"
    assert result.mcp_transport == "stdio_process"
    assert result.mcp_read_status == "transport_unavailable"
    assert result.mcp_transport_error == "down"
    assert result.mcp_endpoint_auth_state == "not_required"


def test_external_context_chat_can_reuse_selected_snapshot_without_true_external_mcp_read(monkeypatch) -> None:
    monkeypatch.setattr(
        research_external_context_service,
        "run_tool_assisted_research_chat",
        lambda **_: _build_internal_result(),
    )
    monkeypatch.setattr(
        research_external_context_service,
        "require_workspace_connector_consent",
        lambda **_: object(),
    )
    _patch_endpoint_state(monkeypatch)

    def fail_read(**kwargs):
        raise AssertionError("read_workspace_true_external_mcp_resource should not be called when a snapshot is selected")

    monkeypatch.setattr(research_external_context_service, "read_workspace_true_external_mcp_resource", fail_read)

    fake_interface = FakeModelInterface(
        text="The selected external snapshot confirms the workspace signal.",
        calls=[],
    )
    monkeypatch.setattr(research_external_context_service, "get_chat_model_interface", lambda: fake_interface)

    snapshot = ResearchExternalResourceSnapshotResponse.model_validate(
        {
            "id": "snapshot-1",
            "workspace_id": "workspace-1",
            "conversation_id": "conversation-1",
            "created_by": "user-1",
            "connector_id": "research_external_context",
            "source_run_id": None,
            "title": "Latest approved market snapshot",
            "analysis_focus": "Judge the strongest market signal",
            "search_query": "pricing pressure market signal",
            "resource_count": 1,
            "resources": [
                {
                    "resource_id": "external-1",
                    "title": "Analyst note",
                    "source_label": "External market note",
                    "snippet": "External analysts also see sustained pricing pressure.",
                }
            ],
            "created_at": "2026-04-02T00:00:00Z",
            "updated_at": "2026-04-02T00:00:00Z",
        }
    )

    result = run_research_external_context_chat(
        workspace_id="workspace-1",
        user_id="user-1",
        question="What is the strongest current signal?",
        selected_external_resource_snapshot=snapshot,
    )

    assert result.degraded_reason is None
    assert result.external_context_used is True
    assert result.selected_external_resource_snapshot_id == "snapshot-1"
    assert result.external_match_count == 1
    assert result.sources[-1].source_kind == "external_context"
    assert len(fake_interface.calls) == 1
    assert result.context_selection_mode == "snapshot"
    assert result.mcp_transport == "stdio_process"
    assert result.mcp_read_status == "snapshot_reused"
    assert result.mcp_transport_error is None
    assert result.mcp_endpoint_auth_state == "not_required"
