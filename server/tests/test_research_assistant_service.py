import pytest

from app.services.research_assistant_service import (
    ResearchAssistantContractError,
    build_research_task_result,
    normalize_research_task_input,
    resolve_research_task_input,
)


def test_normalize_research_task_input_trims_structured_payload() -> None:
    normalized = normalize_research_task_input(
        {
            "goal": "  Build a project brief  ",
            "focus_areas": [" Risks ", "Timeline", "Risks"],
            "key_questions": [" What slipped? ", "Who owns follow-up?"],
            "constraints": ["Use indexed docs only", " Use indexed docs only "],
            "deliverable": "report",
            "requested_sections": ["summary", "findings", "summary"],
        },
    )

    assert normalized == {
        "goal": "Build a project brief",
        "focus_areas": ["Risks", "Timeline"],
        "key_questions": ["What slipped?", "Who owns follow-up?"],
        "constraints": ["Use indexed docs only"],
        "deliverable": "report",
        "requested_sections": ["summary", "findings"],
    }


def test_resolve_research_task_input_applies_defaults_for_summary_task() -> None:
    resolved = resolve_research_task_input(
        task_type="research_summary",
        input_json={"goal": "Summarize the workspace"},
    )

    assert resolved.goal == "Summarize the workspace"
    assert resolved.deliverable == "brief"
    assert resolved.requested_sections == ["summary", "findings", "evidence", "next_steps"]


def test_normalize_research_task_input_rejects_invalid_shapes() -> None:
    with pytest.raises(ResearchAssistantContractError, match="Invalid research task input"):
        normalize_research_task_input(
            {
                "goal": "Summarize the workspace",
                "key_questions": [{"question": "bad"}],
            },
        )


def test_build_research_task_result_includes_structured_contract_and_sections() -> None:
    result = build_research_task_result(
        task_type="workspace_report",
        research_input={
            "goal": "Build a workspace report",
            "focus_areas": ["Timeline"],
            "key_questions": ["What slipped?", "What evidence is strongest?"],
            "deliverable": "report",
        },
        documents=[
            {
                "id": "doc-1",
                "title": "apollo.md",
                "status": "indexed",
                "source_type": "upload",
                "mime_type": "text/markdown",
            },
        ],
        matches=[
            {
                "document_id": "doc-1",
                "chunk_id": "chunk-1",
                "document_title": "apollo.md",
                "chunk_index": 0,
                "snippet": "Delivery slipped by two weeks because sign-off moved.",
            },
        ],
        tool_call_ids=["tool-1", "tool-2"],
    )

    assert result["input"]["goal"] == "Build a workspace report"
    assert result["input"]["deliverable"] == "report"
    assert result["sections"]["findings"][0]["title"] == "apollo.md"
    assert result["sections"]["findings"][0]["evidence_ref_ids"] == ["chunk-1"]
    assert result["sections"]["evidence_overview"][0].startswith("apollo.md:")
    assert result["sections"]["open_questions"] == ["What evidence is strongest?"]
    assert result["metadata"]["focus_area_count"] == 1
