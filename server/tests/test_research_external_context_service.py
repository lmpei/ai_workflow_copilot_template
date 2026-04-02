from dataclasses import dataclass

from app.schemas.chat import ChatToolStep, SourceReference
from app.schemas.mcp import (
    LocalMcpResourceItem,
    LocalMcpResourceReadResult,
    McpResourceDefinition,
    McpServerDefinition,
)
from app.schemas.research_external_resource_snapshot import ResearchExternalResourceSnapshotResponse
from app.services import research_external_context_service
from app.services.mcp_service import (
    RESEARCH_CONTEXT_DIGEST_RESOURCE_ID,
    RESEARCH_CONTEXT_LOCAL_MCP_SERVER_ID,
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


def _build_mcp_read_result() -> LocalMcpResourceReadResult:
    return LocalMcpResourceReadResult(
        server=McpServerDefinition(
            id=RESEARCH_CONTEXT_LOCAL_MCP_SERVER_ID,
            display_name="Research 本地 MCP 服务",
            summary="Bounded MCP pilot",
            transport="local_inproc",
            module_types=["research"],
            resource_ids=[RESEARCH_CONTEXT_DIGEST_RESOURCE_ID],
        ),
        resource=McpResourceDefinition(
            id=RESEARCH_CONTEXT_DIGEST_RESOURCE_ID,
            uri="mcp://research-context/digest",
            display_name="Research 外部上下文摘要",
            summary="Bounded MCP digest",
            mime_type="text/markdown",
            module_types=["research"],
            connector_id="research_external_context",
        ),
        text="## Analyst note\n来源：External market note\n\nExternal analysts also see sustained pricing pressure.",
        resource_count=1,
        items=(
            LocalMcpResourceItem(
                resource_id="market-cost-pressure",
                title="Analyst note",
                source_label="External market note",
                snippet="External analysts also see sustained pricing pressure.",
            ),
        ),
    )


def test_external_context_chat_degrades_honestly_when_consent_is_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        research_external_context_service,
        "run_tool_assisted_research_chat",
        lambda **_: _build_internal_result(),
    )

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
    assert "没有使用 MCP 资源" in result.answer
    assert result.tool_steps[-1].tool_name == "research_external_context"
    assert result.context_selection_mode == "mcp_resource"


def test_external_context_chat_combines_internal_and_mcp_sources(monkeypatch) -> None:
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
        "read_workspace_mcp_resource",
        lambda **_: _build_mcp_read_result(),
    )
    fake_interface = FakeModelInterface(
        text="Workspace material shows pricing pressure, and the MCP resource confirms it is market-wide.",
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
    assert len(result.sources) == 2
    assert result.sources[0].source_kind == "workspace_document"
    assert result.sources[1].source_kind == "external_context"
    assert result.tool_steps[-1].tool_name == "research_external_context"
    assert len(fake_interface.calls) == 1
    assert result.mcp_server_id == RESEARCH_CONTEXT_LOCAL_MCP_SERVER_ID
    assert result.mcp_resource_id == RESEARCH_CONTEXT_DIGEST_RESOURCE_ID
    assert result.context_selection_mode == "mcp_resource"


def test_external_context_chat_degrades_honestly_when_consent_is_revoked(monkeypatch) -> None:
    monkeypatch.setattr(
        research_external_context_service,
        "run_tool_assisted_research_chat",
        lambda **_: _build_internal_result(),
    )

    def require_consent(**kwargs):
        raise research_external_context_service.ConnectorConsentRequiredError(
            "consent revoked",
            consent_state="revoked",
        )

    monkeypatch.setattr(research_external_context_service, "require_workspace_connector_consent", require_consent)

    result = run_research_external_context_chat(
        workspace_id="workspace-1",
        user_id="user-1",
        question="What is the strongest current signal?",
    )

    assert result.degraded_reason == "connector_consent_revoked"
    assert result.external_context_used is False
    assert result.connector_consent_state == "revoked"


def test_external_context_chat_degrades_when_mcp_resource_is_unavailable(monkeypatch) -> None:
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

    def unavailable(**kwargs):
        raise McpValidationError("down")

    monkeypatch.setattr(research_external_context_service, "read_workspace_mcp_resource", unavailable)

    result = run_research_external_context_chat(
        workspace_id="workspace-1",
        user_id="user-1",
        question="What is the strongest current signal?",
    )

    assert result.degraded_reason == "external_context_unavailable"
    assert result.external_context_used is False
    assert result.tool_steps[-1].tool_name == "research_external_context"
    assert result.context_selection_mode == "mcp_resource"


def test_external_context_chat_can_reuse_selected_snapshot_without_mcp_read(monkeypatch) -> None:
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

    def fail_read(**kwargs):
        raise AssertionError("read_workspace_mcp_resource should not be called when a snapshot is selected")

    monkeypatch.setattr(research_external_context_service, "read_workspace_mcp_resource", fail_read)

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
