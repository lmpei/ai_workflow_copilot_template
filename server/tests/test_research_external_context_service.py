from dataclasses import dataclass

from app.connectors.research_external_context_connector import (
    ResearchExternalContextConnectorUnavailableError,
    ResearchExternalContextEntry,
)
from app.schemas.chat import ChatToolStep, SourceReference
from app.services import research_external_context_service
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


def test_external_context_chat_degrades_honestly_when_consent_is_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        research_external_context_service,
        "run_tool_assisted_research_chat",
        lambda **_: _build_internal_result(),
    )

    def require_consent(**kwargs):
        raise research_external_context_service.ConnectorConsentRequiredError("consent required")

    monkeypatch.setattr(research_external_context_service, "require_workspace_connector_consent", require_consent)

    result = run_research_external_context_chat(
        workspace_id="workspace-1",
        user_id="user-1",
        question="What is the strongest current signal?",
    )

    assert result.degraded_reason == "connector_consent_required"
    assert result.external_context_used is False
    assert result.connector_consent_state == "not_granted"
    assert "has not granted consent" in result.answer
    assert result.tool_steps[-1].tool_name == "research_external_context"


def test_external_context_chat_combines_internal_and_external_sources(monkeypatch) -> None:
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
        "search_research_external_context",
        lambda **_: [
            ResearchExternalContextEntry(
                context_id="external-1",
                title="Analyst note",
                source_label="External market note",
                keywords=("pricing", "pressure"),
                snippet="External analysts also see sustained pricing pressure.",
            )
        ],
    )
    fake_interface = FakeModelInterface(
        text="Workspace material shows pricing pressure, and external context confirms it is market-wide.",
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


def test_external_context_chat_degrades_when_connector_is_unavailable(monkeypatch) -> None:
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
        raise ResearchExternalContextConnectorUnavailableError("down")

    monkeypatch.setattr(research_external_context_service, "search_research_external_context", unavailable)

    result = run_research_external_context_chat(
        workspace_id="workspace-1",
        user_id="user-1",
        question="What is the strongest current signal?",
    )

    assert result.degraded_reason == "external_context_unavailable"
    assert result.external_context_used is False
    assert "unavailable during this pass" in result.answer
