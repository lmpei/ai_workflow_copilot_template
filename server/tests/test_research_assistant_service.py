import pytest

from app.services.research_assistant_service import (
    ResearchAssistantContractError,
    build_research_task_result,
    evaluate_research_result_regression,
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
            "parent_task_id": "  task-123  ",
            "continuation_notes": "  Compare against the previous report  ",
        },
    )

    assert normalized == {
        "goal": "Build a project brief",
        "focus_areas": ["Risks", "Timeline"],
        "key_questions": ["What slipped?", "Who owns follow-up?"],
        "constraints": ["Use indexed docs only"],
        "deliverable": "report",
        "requested_sections": ["summary", "findings"],
        "parent_task_id": "task-123",
        "continuation_notes": "Compare against the previous report",
    }


def test_resolve_research_task_input_applies_defaults_for_summary_task() -> None:
    resolved = resolve_research_task_input(
        task_type="research_summary",
        input_json={"goal": "Summarize the workspace"},
    )

    assert resolved.goal == "Summarize the workspace"
    assert resolved.deliverable == "brief"
    assert resolved.requested_sections == ["summary", "findings", "evidence", "next_steps"]
    assert resolved.parent_task_id is None


def test_normalize_research_task_input_rejects_invalid_shapes() -> None:
    with pytest.raises(ResearchAssistantContractError, match="Research 任务输入无效"):
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
    assert result["metadata"]["evidence_status"] == "grounded_matches"
    assert result["metadata"]["regression_passed"] is True
    assert result["metadata"]["regression_baseline"]["baseline_version"] == "stage_a_research_regression_v1"
    assert result["metadata"]["regression_baseline"]["signals"]["evidence_status"] == "grounded_matches"
    assert result["metadata"]["trust"]["baseline_version"] == "stage_a_research_v1"
    assert result["metadata"]["trust"]["checks"]["grounded_findings_when_matches_exist"] is True


def test_build_research_task_result_builds_formal_report_for_workspace_report() -> None:
    result = build_research_task_result(
        task_type="workspace_report",
        research_input={
            "goal": "Build a grounded project report",
            "deliverable": "report",
            "requested_sections": ["findings", "evidence", "open_questions", "next_steps"],
            "key_questions": ["What slipped?", "Which risk needs more support?"],
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
        tool_call_ids=["tool-1"],
    )

    report = result["report"]

    assert report["headline"] == "Research Report: Build a grounded project report"
    assert report["executive_summary"] == result["sections"]["summary"]
    assert [section["slug"] for section in report["sections"]] == [
        "findings",
        "evidence",
        "open-questions",
        "next-steps",
    ]
    assert report["sections"][0]["evidence_ref_ids"] == ["chunk-1"]
    assert report["evidence_ref_ids"] == ["chunk-1"]
    assert report["open_questions"] == ["Which risk needs more support?"]
    assert result["metadata"]["report_ready"] is True
    assert result["metadata"]["trust"]["report_requested"] is True
    assert result["metadata"]["trust"]["report_section_count"] == 4


def test_build_research_task_result_carries_follow_up_lineage() -> None:
    result = build_research_task_result(
        task_type="workspace_report",
        research_input={
            "goal": "Revisit the strongest project risks",
            "deliverable": "report",
            "parent_task_id": "task-parent",
            "continuation_notes": "Focus on which risk still lacks support.",
        },
        lineage={
            "parent_task_id": "task-parent",
            "parent_task_type": "workspace_report",
            "parent_title": "Workspace Report",
            "parent_goal": "Build a grounded workspace report",
            "parent_summary": "Delayed sign-off is the strongest current risk.",
            "parent_report_headline": "Research Report: Build a grounded workspace report",
            "continuation_notes": "Focus on which risk still lacks support.",
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
                "snippet": "Delayed sign-off remains the strongest grounded risk.",
            },
        ],
        tool_call_ids=["tool-1"],
    )

    assert result["lineage"]["parent_task_id"] == "task-parent"
    assert result["lineage"]["parent_goal"] == "Build a grounded workspace report"
    assert result["report"]["headline"] == "Research Follow-up Report: Revisit the strongest project risks"
    assert result["sections"]["open_questions"][0] == "Focus on which risk still lacks support."
    assert result["sections"]["next_steps"][0] == "Compare this run against parent research task task-parent."
    assert result["metadata"]["is_follow_up"] is True
    assert result["metadata"]["parent_task_id"] == "task-parent"
    assert result["metadata"]["trust"]["is_follow_up"] is True
    assert result["metadata"]["regression_baseline"]["checks"]["lineage_present_for_follow_up"] is True


def test_build_research_task_result_keeps_report_coherent_when_matches_are_missing() -> None:
    result = build_research_task_result(
        task_type="workspace_report",
        research_input={
            "goal": "Build a report from limited context",
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
        matches=[],
        tool_call_ids=["tool-1"],
    )

    report = result["report"]

    assert report["headline"] == "Research Report: Build a report from limited context"
    assert report["sections"][0]["slug"] == "findings"
    assert report["sections"][0]["bullets"] == [
        "apollo.md: Document is available with status indexed.",
    ]
    assert report["sections"][1]["slug"] == "evidence"
    assert report["sections"][1]["evidence_ref_ids"] == ["doc-1"]
    assert report["open_questions"] == [
        "Which query or focus area would narrow the search toward stronger evidence?",
    ]
    assert report["recommended_next_steps"][0].startswith("Add a clearer research goal")
    assert result["metadata"]["report_ready"] is True
    assert result["metadata"]["evidence_status"] == "documents_only"
    assert result["metadata"]["regression_passed"] is False
    assert result["metadata"]["regression_baseline"]["issues"] == ["weak_evidence_documents_only"]
    assert result["metadata"]["trust_gaps"] == ["no_grounded_matches"]
    assert result["metadata"]["trust"]["regression_passed"] is False


def test_evaluate_research_result_regression_flags_incomplete_report_shape() -> None:
    baseline = evaluate_research_result_regression(
        {
            "module_type": "research",
            "task_type": "workspace_report",
            "summary": "A draft summary exists.",
            "input": {"deliverable": "report"},
            "sections": {
                "summary": "A draft summary exists.",
                "findings": [],
                "evidence_overview": [],
                "open_questions": [],
                "next_steps": [],
            },
            "artifacts": {
                "document_count": 1,
                "match_count": 0,
                "documents": [],
                "matches": [],
                "tool_call_ids": [],
            },
            "metadata": {
                "evidence_status": "documents_only",
                "trust_gaps": ["no_grounded_matches"],
            },
        },
    )

    assert baseline["baseline_version"] == "stage_a_research_regression_v1"
    assert baseline["passed"] is False
    assert "missing_trust_metadata" in baseline["issues"]
    assert "unexpected_trust_baseline" in baseline["issues"]
    assert "missing_report" in baseline["issues"]
    assert "invalid_report_shape" in baseline["issues"]
