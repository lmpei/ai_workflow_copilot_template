from uuid import uuid4

import pytest

from app.core.database import reset_database_for_tests
from app.models.document import DOCUMENT_STATUS_INDEXED
from app.repositories import document_repository, task_repository
from app.repositories.user_repository import create_user
from app.repositories.workspace_repository import create_workspace
from app.schemas.workspace import WorkspaceCreate
from app.services.agent_service import (
    AgentAccessError,
    AgentRuntimeError,
    run_workspace_job_agent,
    run_workspace_research_agent,
    run_workspace_support_agent,
)
from app.services.retrieval_service import RetrievedChunk


@pytest.fixture(autouse=True)
def reset_database() -> None:
    reset_database_for_tests()



def _create_runtime_fixture(
    *,
    with_document: bool = True,
    workspace_type: str = "research",
    task_type: str = "research_summary",
    input_json: dict[str, object] | None = None,
) -> tuple[str, str, str]:
    unique_suffix = uuid4().hex
    user = create_user(
        email=f"phase3-agent-{unique_suffix}@example.com",
        password_hash="not-used-in-this-test",
        name="Phase 3 Agent",
    )
    workspace = create_workspace(
        WorkspaceCreate(name="Phase 3 Agent Workspace", module_type=workspace_type),
        owner_id=user.id,
    )
    task = task_repository.create_task(
        workspace_id=workspace.id,
        task_type=task_type,
        created_by=user.id,
        input_json=input_json or {"goal": "Summarize workspace findings"},
    )
    if with_document:
        document_repository.create_document(
            document_id=str(uuid4()),
            workspace_id=workspace.id,
            title="demo.txt",
            file_path="uploads/demo.txt",
            mime_type="text/plain",
            created_by=user.id,
            status=DOCUMENT_STATUS_INDEXED,
        )
    return user.id, workspace.id, task.id


def _create_completed_job_review_task(
    *,
    workspace_id: str,
    user_id: str,
    target_role: str,
    candidate_label: str,
    summary: str,
    fit_signal: str = "grounded_match_found",
    evidence_status: str = "grounded_matches",
    recommended_outcome: str = "advance_to_manual_review",
) -> str:
    task = task_repository.create_task(
        workspace_id=workspace_id,
        task_type="resume_match",
        created_by=user_id,
        input_json={
            "target_role": target_role,
            "candidate_label": candidate_label,
        },
    )
    running_task = task_repository.update_task_status(task.id, next_status="running")
    assert running_task is not None
    completed_task = task_repository.update_task_status(
        task.id,
        next_status="done",
        output_json={
            "result": {
                "module_type": "job",
                "task_type": "resume_match",
                "title": "Structured Resume Match Review",
                "summary": summary,
                "input": {
                    "target_role": target_role,
                    "candidate_label": candidate_label,
                    "comparison_task_ids": [],
                },
                "review_brief": {
                    "role_summary": target_role,
                    "candidate_label": candidate_label,
                    "must_have_skills": [],
                    "preferred_skills": [],
                    "evidence_status": evidence_status,
                    "comparison_task_count": 0,
                },
                "findings": [
                    {
                        "title": f"{candidate_label} signal",
                        "summary": summary,
                        "evidence_ref_ids": [f"{task.id}-chunk"],
                    }
                ],
                "gaps": [],
                "assessment": {
                    "fit_signal": fit_signal,
                    "evidence_status": evidence_status,
                    "recommended_outcome": recommended_outcome,
                    "confidence_note": "Stored comparison fixture.",
                    "rationale": "Stored comparison fixture.",
                },
                "comparison_candidates": [],
                "open_questions": [],
                "next_steps": [],
                "highlights": [summary],
                "evidence": [],
                "artifacts": {
                    "document_count": 1,
                    "match_count": 1,
                    "documents": [],
                    "matches": [],
                    "tool_call_ids": [],
                    "evidence_status": evidence_status,
                    "fit_signal": fit_signal,
                    "recommended_next_step": "Review this candidate manually.",
                },
                "metadata": {
                    "target_role": target_role,
                    "candidate_label": candidate_label,
                    "shortlist_ready": False,
                },
            }
        },
    )
    assert completed_task is not None
    return task.id



def test_workspace_research_agent_completes_tool_using_workflow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeRetriever:
        def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
            assert workspace_id
            assert question == "Who owns the project?"
            return [
                RetrievedChunk(
                    document_id="doc-1",
                    chunk_id="chunk-1",
                    document_title="demo.txt",
                    chunk_index=0,
                    snippet="The owner is Alice.",
                    content="The owner is Alice.",
                ),
            ]

    monkeypatch.setattr("app.agents.tool_registry.get_retriever", lambda: FakeRetriever())

    user_id, workspace_id, task_id = _create_runtime_fixture()

    result = run_workspace_research_agent(
        task_id=task_id,
        workspace_id=workspace_id,
        user_id=user_id,
        goal="Who owns the project?",
    )

    assert result.agent_name == "workspace_research_agent"
    assert result.final_output["module_type"] == "research"
    assert result.final_output["task_type"] == "research_summary"
    assert result.final_output["title"] == "Research Summary"
    assert result.final_output["summary"].startswith("Reviewed 1 workspace document")
    assert result.final_output["input"]["goal"] == "Who owns the project?"
    assert result.final_output["input"]["deliverable"] == "brief"
    assert result.final_output["highlights"] == ["demo.txt: The owner is Alice."]
    assert result.final_output["sections"]["findings"][0]["title"] == "demo.txt"
    assert result.final_output["sections"]["findings"][0]["evidence_ref_ids"] == ["chunk-1"]
    assert result.final_output["artifacts"]["document_count"] == 1
    assert result.final_output["artifacts"]["match_count"] == 1
    assert result.final_output["artifacts"]["matches"][0]["document_title"] == "demo.txt"
    assert result.final_output["evidence"][0]["metadata"]["document_id"] == "doc-1"
    assert result.final_output["metadata"]["goal"] == "Who owns the project?"

    agent_runs = task_repository.list_task_agent_runs(task_id)
    assert len(agent_runs) == 1
    assert agent_runs[0].status == "completed"
    assert agent_runs[0].final_output == result.final_output

    tool_calls = task_repository.list_agent_run_tool_calls(result.agent_run_id)
    assert [tool_call.tool_name for tool_call in tool_calls] == [
        "list_workspace_documents",
        "search_documents",
    ]
    assert all(tool_call.status == "completed" for tool_call in tool_calls)



def test_workspace_research_agent_completes_with_minimal_available_context() -> None:
    user_id, workspace_id, task_id = _create_runtime_fixture(with_document=False)

    result = run_workspace_research_agent(
        task_id=task_id,
        workspace_id=workspace_id,
        user_id=user_id,
        goal="Summarize this workspace",
    )

    assert result.final_output["module_type"] == "research"
    assert result.final_output["input"]["deliverable"] == "brief"
    assert result.final_output["artifacts"]["document_count"] == 0
    assert result.final_output["artifacts"]["match_count"] == 0
    assert result.final_output["artifacts"]["matches"] == []
    assert result.final_output["evidence"] == []
    assert result.final_output["sections"]["findings"] == []
    assert result.final_output["sections"]["next_steps"][0].startswith("Upload or index")
    assert result.final_output["summary"] == "No workspace documents are available for analysis."

    tool_calls = task_repository.list_agent_run_tool_calls(result.agent_run_id)
    assert [tool_call.tool_name for tool_call in tool_calls] == ["list_workspace_documents"]
    assert tool_calls[0].status == "completed"



def test_workspace_research_agent_builds_formal_report_for_workspace_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeRetriever:
        def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
            assert workspace_id
            assert question == "Build a grounded workspace report"
            return [
                RetrievedChunk(
                    document_id="doc-1",
                    chunk_id="chunk-1",
                    document_title="demo.txt",
                    chunk_index=0,
                    snippet="The strongest delivery risk is delayed stakeholder sign-off.",
                    content="The strongest delivery risk is delayed stakeholder sign-off.",
                ),
            ]

    monkeypatch.setattr("app.agents.tool_registry.get_retriever", lambda: FakeRetriever())

    research_input = {
        "goal": "Build a grounded workspace report",
        "deliverable": "report",
        "key_questions": ["What slipped?", "What needs more evidence?"],
    }
    user_id, workspace_id, task_id = _create_runtime_fixture(
        task_type="workspace_report",
        input_json=research_input,
    )

    result = run_workspace_research_agent(
        task_id=task_id,
        workspace_id=workspace_id,
        user_id=user_id,
        goal="Build a grounded workspace report",
        research_input=research_input,
    )

    assert result.final_output["task_type"] == "workspace_report"
    assert result.final_output["report"]["headline"] == "Research Report: Build a grounded workspace report"
    assert result.final_output["report"]["sections"][0]["slug"] == "findings"
    assert result.final_output["report"]["sections"][0]["evidence_ref_ids"] == ["chunk-1"]
    assert result.final_output["metadata"]["report_ready"] is True

    tool_calls = task_repository.list_agent_run_tool_calls(result.agent_run_id)
    assert [tool_call.tool_name for tool_call in tool_calls] == [
        "list_workspace_documents",
        "search_documents",
    ]


def test_workspace_research_agent_includes_follow_up_lineage_in_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeRetriever:
        def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
            assert workspace_id
            assert "Continue the prior research run" in question
            return [
                RetrievedChunk(
                    document_id="doc-1",
                    chunk_id="chunk-1",
                    document_title="demo.txt",
                    chunk_index=0,
                    snippet="The strongest risk still lacks owner-level evidence.",
                    content="The strongest risk still lacks owner-level evidence.",
                ),
            ]

    monkeypatch.setattr("app.agents.tool_registry.get_retriever", lambda: FakeRetriever())

    research_input = {
        "goal": "Refine the strongest risk",
        "deliverable": "report",
        "parent_task_id": "task-parent",
        "continuation_notes": "Focus on unresolved evidence gaps.",
    }
    research_lineage = {
        "parent_task_id": "task-parent",
        "parent_task_type": "workspace_report",
        "parent_title": "Workspace Report",
        "parent_goal": "Build a grounded workspace report",
        "parent_summary": "Delayed sign-off is the strongest current risk.",
        "parent_report_headline": "Research Report: Build a grounded workspace report",
        "continuation_notes": "Focus on unresolved evidence gaps.",
    }
    user_id, workspace_id, task_id = _create_runtime_fixture(
        task_type="workspace_report",
        input_json=research_input,
    )

    result = run_workspace_research_agent(
        task_id=task_id,
        workspace_id=workspace_id,
        user_id=user_id,
        goal="Continue the prior research run",
        research_input=research_input,
        research_lineage=research_lineage,
    )

    assert result.final_output["lineage"]["parent_task_id"] == "task-parent"
    assert result.final_output["metadata"]["is_follow_up"] is True
    assert result.final_output["report"]["headline"] == "Research Follow-up Report: Refine the strongest risk"


def test_workspace_support_agent_completes_grounded_reply_draft(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeRetriever:
        def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
            assert workspace_id
            assert question == (
                "Customer cannot reset their password"
                " | Product area: Authentication"
                " | Severity: high"
                " | Desired outcome: Restore access quickly"
                " | Reproduction steps: Open reset email; Click expired link"
            )
            return [
                RetrievedChunk(
                    document_id="doc-1",
                    chunk_id="chunk-1",
                    document_title="support-guide.md",
                    chunk_index=0,
                    snippet=(
                        "Reset links expire after 15 minutes; "
                        "users should request a new email."
                    ),
                    content=(
                        "Reset links expire after 15 minutes; "
                        "users should request a new email."
                    ),
                ),
            ]

    monkeypatch.setattr("app.agents.tool_registry.get_retriever", lambda: FakeRetriever())

    user_id, workspace_id, task_id = _create_runtime_fixture(
        workspace_type="support",
        task_type="reply_draft",
        input_json={
            "customer_issue": "Customer cannot reset their password",
            "product_area": "Authentication",
            "severity": "high",
            "desired_outcome": "Restore access quickly",
            "reproduction_steps": [
                "Open reset email",
                "Click expired link",
            ],
        },
    )

    result = run_workspace_support_agent(
        task_id=task_id,
        workspace_id=workspace_id,
        user_id=user_id,
        customer_issue="Customer cannot reset their password",
        support_input={
            "customer_issue": "Customer cannot reset their password",
            "product_area": "Authentication",
            "severity": "high",
            "desired_outcome": "Restore access quickly",
            "reproduction_steps": [
                "Open reset email",
                "Click expired link",
            ],
        },
    )

    assert result.agent_name == "workspace_support_agent"
    assert result.final_output["module_type"] == "support"
    assert result.final_output["task_type"] == "reply_draft"
    assert result.final_output["title"] == "Grounded Reply Draft"
    assert result.final_output["input"]["product_area"] == "Authentication"
    assert result.final_output["case_brief"]["severity"] == "high"
    assert result.final_output["triage"]["recommended_owner"] == "support_escalation"
    assert result.final_output["triage"]["should_escalate"] is True
    assert result.final_output["findings"][0]["evidence_ref_ids"] == ["chunk-1"]
    assert result.final_output["reply_draft"]["subject_line"] == "Support update for your reported issue"
    assert "indexed support guidance" in result.final_output["reply_draft"]["body"]
    assert result.final_output["artifacts"]["document_count"] == 1
    assert result.final_output["artifacts"]["match_count"] == 1
    assert result.final_output["artifacts"]["evidence_status"] == "grounded_matches"
    assert result.final_output["evidence"][0]["metadata"]["document_id"] == "doc-1"
    assert (
        result.final_output["metadata"]["customer_issue"]
        == "Customer cannot reset their password"
    )

    tool_calls = task_repository.list_agent_run_tool_calls(result.agent_run_id)
    assert [tool_call.tool_name for tool_call in tool_calls] == [
        "list_workspace_documents",
        "search_documents",
    ]



def test_workspace_support_agent_includes_follow_up_lineage_and_escalation_packet(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeRetriever:
        def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
            assert workspace_id
            assert question == (
                "Continue the prior support case 'Grounded Reply Draft'. "
                "Prior summary: Grounded password reset guidance was found for the case. "
                "Prior recommended owner: support_escalation "
                "Follow-up guidance: Confirm whether the reset link can be reissued safely. "
                "Current request: Customer cannot reset their password | Product area: Authentication | Severity: high"
            )
            return [
                RetrievedChunk(
                    document_id="doc-1",
                    chunk_id="chunk-1",
                    document_title="support-guide.md",
                    chunk_index=0,
                    snippet="Reset links can be reissued safely after identity verification.",
                    content="Reset links can be reissued safely after identity verification.",
                ),
            ]

    monkeypatch.setattr("app.agents.tool_registry.get_retriever", lambda: FakeRetriever())

    unique_suffix = uuid4().hex
    user = create_user(
        email=f"support-follow-up-agent-{unique_suffix}@example.com",
        password_hash="not-used-in-this-test",
        name="Support Follow Up Agent",
    )
    workspace = create_workspace(
        WorkspaceCreate(name="Support Follow Up Workspace", module_type="support"),
        owner_id=user.id,
    )
    document_repository.create_document(
        document_id=str(uuid4()),
        workspace_id=workspace.id,
        title="support-guide.md",
        file_path="uploads/support-guide.md",
        mime_type="text/markdown",
        created_by=user.id,
        status=DOCUMENT_STATUS_INDEXED,
    )
    parent_task = task_repository.create_task(
        workspace_id=workspace.id,
        task_type="reply_draft",
        created_by=user.id,
        input_json={
            "customer_issue": "Customer cannot reset their password",
            "product_area": "Authentication",
            "severity": "high",
        },
    )
    running_parent = task_repository.update_task_status(parent_task.id, next_status="running")
    assert running_parent is not None
    completed_parent = task_repository.update_task_status(
        parent_task.id,
        next_status="done",
        output_json={
            "result": {
                "module_type": "support",
                "task_type": "reply_draft",
                "title": "Grounded Reply Draft",
                "summary": "Grounded password reset guidance was found for the case.",
                "input": {
                    "customer_issue": "Customer cannot reset their password",
                    "product_area": "Authentication",
                    "severity": "high",
                },
                "triage": {
                    "evidence_status": "grounded_matches",
                    "needs_manual_review": True,
                    "should_escalate": True,
                    "recommended_owner": "support_escalation",
                    "rationale": "Human review is required before updating the customer.",
                },
            },
        },
    )
    assert completed_parent is not None

    follow_up_task = task_repository.create_task(
        workspace_id=workspace.id,
        task_type="reply_draft",
        created_by=user.id,
        input_json={
            "parent_task_id": parent_task.id,
            "follow_up_notes": "Confirm whether the reset link can be reissued safely.",
        },
    )

    result = run_workspace_support_agent(
        task_id=follow_up_task.id,
        workspace_id=workspace.id,
        user_id=user.id,
        customer_issue="Continue the current support case",
        support_input={
            "parent_task_id": parent_task.id,
            "follow_up_notes": "Confirm whether the reset link can be reissued safely.",
        },
    )

    assert result.final_output["lineage"]["parent_task_id"] == parent_task.id
    assert result.final_output["input"]["customer_issue"] == "Customer cannot reset their password"
    assert result.final_output["metadata"]["is_follow_up"] is True
    assert result.final_output["triage"]["recommended_owner"] == "support_escalation"
    assert result.final_output["escalation_packet"]["follow_up_notes"] == "Confirm whether the reset link can be reissued safely."
    assert result.final_output["escalation_packet"]["evidence_status"] == "grounded_matches"


def test_workspace_support_agent_returns_bounded_shape_without_documents() -> None:
    user_id, workspace_id, task_id = _create_runtime_fixture(
        with_document=False,
        workspace_type="support",
        task_type="ticket_summary",
        input_json={
            "customer_issue": "Customer billing question",
            "desired_outcome": "Confirm next billing step",
        },
    )

    result = run_workspace_support_agent(
        task_id=task_id,
        workspace_id=workspace_id,
        user_id=user_id,
        customer_issue="Customer billing question",
        support_input={
            "customer_issue": "Customer billing question",
            "desired_outcome": "Confirm next billing step",
        },
    )

    assert result.final_output["module_type"] == "support"
    assert result.final_output["case_brief"]["desired_outcome"] == "Confirm next billing step"
    assert result.final_output["triage"]["recommended_owner"] == "knowledge_base_owner"
    assert result.final_output["triage"]["should_escalate"] is True
    assert result.final_output["open_questions"][0] == "Which product area or feature is affected?"
    assert result.final_output["next_steps"][0].startswith("Index support runbooks")
    assert result.final_output["artifacts"]["document_count"] == 0
    assert result.final_output["artifacts"]["match_count"] == 0
    assert result.final_output["artifacts"]["matches"] == []
    assert result.final_output["artifacts"]["evidence_status"] == "no_documents"
    assert (
        result.final_output["summary"]
        == "No support knowledge documents are available for this workspace."
    )
    assert result.final_output["evidence"] == []


def test_workspace_job_agent_completes_resume_match_with_grounded_signal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeRetriever:
        def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
            assert workspace_id
            assert question == (
                "Platform engineer"
                " | Seniority: senior"
                " | Must-have skills: Python, API design"
                " | Preferred skills: Reliability"
                " | Hiring context: Core platform modernization"
            )
            return [
                RetrievedChunk(
                    document_id="doc-1",
                    chunk_id="chunk-1",
                    document_title="candidate_resume.md",
                    chunk_index=0,
                    snippet=(
                        "Strong Python backend experience "
                        "with API design and reliability work."
                    ),
                    content=(
                        "Strong Python backend experience "
                        "with API design and reliability work."
                    ),
                ),
            ]

    monkeypatch.setattr("app.agents.tool_registry.get_retriever", lambda: FakeRetriever())

    user_id, workspace_id, task_id = _create_runtime_fixture(
        workspace_type="job",
        task_type="resume_match",
        input_json={
            "target_role": "Platform engineer",
            "seniority": "senior",
            "must_have_skills": ["Python", "API design"],
            "preferred_skills": ["Reliability"],
            "hiring_context": "Core platform modernization",
        },
    )

    result = run_workspace_job_agent(
        task_id=task_id,
        workspace_id=workspace_id,
        user_id=user_id,
        target_role="Platform engineer",
        job_input={
            "target_role": "Platform engineer",
            "seniority": "senior",
            "must_have_skills": ["Python", "API design"],
            "preferred_skills": ["Reliability"],
            "hiring_context": "Core platform modernization",
        },
    )

    assert result.agent_name == "workspace_job_agent"
    assert result.final_output["module_type"] == "job"
    assert result.final_output["task_type"] == "resume_match"
    assert result.final_output["input"]["seniority"] == "senior"
    assert result.final_output["review_brief"]["must_have_skills"] == ["Python", "API design"]
    assert result.final_output["findings"][0]["evidence_ref_ids"] == ["chunk-1"]
    assert result.final_output["assessment"]["recommended_outcome"] == "advance_to_manual_review"
    assert "Grounded candidate evidence" in result.final_output["assessment"]["confidence_note"]
    assert result.final_output["artifacts"]["fit_signal"] == "grounded_match_found"
    assert result.final_output["artifacts"]["recommended_next_step"].startswith(
        "Review the grounded fit evidence",
    )
    assert result.final_output["artifacts"]["evidence_status"] == "grounded_matches"
    assert result.final_output["evidence"][0]["metadata"]["document_id"] == "doc-1"
    assert result.final_output["metadata"]["target_role"] == "Platform engineer"

    tool_calls = task_repository.list_agent_run_tool_calls(result.agent_run_id)
    assert [tool_call.tool_name for tool_call in tool_calls] == [
        "list_workspace_documents",
        "search_documents",
    ]


def test_workspace_job_agent_returns_bounded_shape_without_documents() -> None:
    user_id, workspace_id, task_id = _create_runtime_fixture(
        with_document=False,
        workspace_type="job",
        task_type="jd_summary",
        input_json={
            "target_role": "Platform engineer",
            "seniority": "mid",
        },
    )

    result = run_workspace_job_agent(
        task_id=task_id,
        workspace_id=workspace_id,
        user_id=user_id,
        target_role="Platform engineer",
        job_input={
            "target_role": "Platform engineer",
            "seniority": "mid",
        },
    )

    assert result.final_output["module_type"] == "job"
    assert result.final_output["review_brief"]["seniority"] == "mid"
    assert result.final_output["assessment"]["recommended_outcome"] == "gather_hiring_materials"
    assert result.final_output["gaps"][0] == "Must-have skills are not specified."
    assert result.final_output["open_questions"][0] == "Which skills are non-negotiable for this hiring decision?"
    assert result.final_output["artifacts"]["document_count"] == 0
    assert result.final_output["artifacts"]["match_count"] == 0
    assert result.final_output["artifacts"]["fit_signal"] == "no_documents_available"
    assert result.final_output["artifacts"]["evidence_status"] == "no_documents"
    assert result.final_output["summary"] == "No job documents are available for this workspace."
    assert result.final_output["evidence"] == []


def test_workspace_job_agent_builds_shortlist_from_completed_candidate_reviews(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeRetriever:
        def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
            assert workspace_id
            assert "Compare these completed candidate reviews for the same hiring decision." in question
            assert "Candidate A: Strong backend ownership with grounded platform evidence." in question
            assert "Candidate B: Clear systems-design signal, but reliability proof is still thin." in question
            assert "Shortlist focus: Prioritize backend ownership and interview risk." in question
            return [
                RetrievedChunk(
                    document_id="doc-1",
                    chunk_id="chunk-1",
                    document_title="hiring-notes.md",
                    chunk_index=0,
                    snippet="Backend ownership matters more than breadth for this role.",
                    content="Backend ownership matters more than breadth for this role.",
                ),
            ]

    monkeypatch.setattr("app.agents.tool_registry.get_retriever", lambda: FakeRetriever())

    unique_suffix = uuid4().hex
    user = create_user(
        email=f"job-shortlist-agent-{unique_suffix}@example.com",
        password_hash="not-used-in-this-test",
        name="Job Shortlist Agent",
    )
    workspace = create_workspace(
        WorkspaceCreate(name="Job Shortlist Workspace", module_type="job"),
        owner_id=user.id,
    )
    document_repository.create_document(
        document_id=str(uuid4()),
        workspace_id=workspace.id,
        title="hiring-notes.md",
        file_path="uploads/hiring-notes.md",
        mime_type="text/markdown",
        created_by=user.id,
        status=DOCUMENT_STATUS_INDEXED,
    )
    candidate_a_task_id = _create_completed_job_review_task(
        workspace_id=workspace.id,
        user_id=user.id,
        target_role="Platform engineer",
        candidate_label="Candidate A",
        summary="Strong backend ownership with grounded platform evidence.",
    )
    candidate_b_task_id = _create_completed_job_review_task(
        workspace_id=workspace.id,
        user_id=user.id,
        target_role="Platform engineer",
        candidate_label="Candidate B",
        summary="Clear systems-design signal, but reliability proof is still thin.",
        fit_signal="insufficient_grounding",
        evidence_status="documents_only",
        recommended_outcome="collect_more_hiring_signal",
    )
    shortlist_task = task_repository.create_task(
        workspace_id=workspace.id,
        task_type="resume_match",
        created_by=user.id,
        input_json={
            "target_role": "Platform engineer",
            "comparison_task_ids": [candidate_a_task_id, candidate_b_task_id],
            "comparison_notes": "Prioritize backend ownership and interview risk.",
        },
    )

    result = run_workspace_job_agent(
        task_id=shortlist_task.id,
        workspace_id=workspace.id,
        user_id=user.id,
        target_role="Platform engineer",
        job_input={
            "target_role": "Platform engineer",
            "comparison_task_ids": [candidate_a_task_id, candidate_b_task_id],
            "comparison_notes": "Prioritize backend ownership and interview risk.",
        },
    )

    assert result.final_output["title"] == "Candidate Comparison Shortlist"
    assert result.final_output["comparison_candidates"][0]["candidate_label"] == "Candidate A"
    assert len(result.final_output["comparison_candidates"]) == 2
    assert result.final_output["shortlist"]["entries"][0]["candidate_label"] == "Candidate A"
    assert result.final_output["shortlist"]["entries"][1]["candidate_label"] == "Candidate B"
    assert result.final_output["shortlist"]["comparison_notes"] == "Prioritize backend ownership and interview risk."
    assert result.final_output["metadata"]["shortlist_ready"] is True
    assert result.final_output["review_brief"]["comparison_task_count"] == 2



def test_workspace_research_agent_marks_agent_run_failed_on_tool_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingRetriever:
        def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
            raise RuntimeError("Chroma unavailable")

    monkeypatch.setattr("app.agents.tool_registry.get_retriever", lambda: FailingRetriever())

    user_id, workspace_id, task_id = _create_runtime_fixture()

    with pytest.raises(AgentRuntimeError) as error:
        run_workspace_research_agent(
            task_id=task_id,
            workspace_id=workspace_id,
            user_id=user_id,
            goal="Who owns the project?",
        )

    assert error.value.agent_run_id is not None
    agent_run = task_repository.get_agent_run(error.value.agent_run_id)
    assert agent_run is not None
    assert agent_run.status == "failed"
    assert agent_run.final_output == {"error": "Chroma unavailable"}

    tool_calls = task_repository.list_agent_run_tool_calls(agent_run.id)
    assert [tool_call.tool_name for tool_call in tool_calls] == [
        "list_workspace_documents",
        "search_documents",
    ]
    assert tool_calls[0].status == "completed"
    assert tool_calls[1].status == "failed"



def test_workspace_research_agent_rejects_foreign_task_access() -> None:
    user_id, workspace_id, task_id = _create_runtime_fixture()

    with pytest.raises(AgentAccessError, match="Task not found"):
        run_workspace_research_agent(
            task_id=task_id,
            workspace_id=workspace_id,
            user_id=str(uuid4()),
            goal="Who owns the project?",
        )



def test_workspace_research_agent_rejects_invalid_module_task_combination() -> None:
    user_id, workspace_id, task_id = _create_runtime_fixture(workspace_type="support")

    with pytest.raises(AgentRuntimeError, match="Task type research_summary is not supported"):
        run_workspace_research_agent(
            task_id=task_id,
            workspace_id=workspace_id,
            user_id=user_id,
            goal="Who owns the project?",
        )



def test_workspace_support_agent_rejects_invalid_module_task_combination() -> None:
    user_id, workspace_id, task_id = _create_runtime_fixture(
        workspace_type="research",
        task_type="ticket_summary",
        input_json={"customer_issue": "Customer billing question"},
    )

    with pytest.raises(AgentRuntimeError, match="Task type ticket_summary is not supported"):
        run_workspace_support_agent(
            task_id=task_id,
            workspace_id=workspace_id,
            user_id=user_id,
            customer_issue="Customer billing question",
        )


def test_workspace_job_agent_rejects_invalid_module_task_combination() -> None:
    user_id, workspace_id, task_id = _create_runtime_fixture(
        workspace_type="research",
        task_type="jd_summary",
        input_json={"target_role": "Platform engineer"},
    )

    with pytest.raises(AgentRuntimeError, match="Task type jd_summary is not supported"):
        run_workspace_job_agent(
            task_id=task_id,
            workspace_id=workspace_id,
            user_id=user_id,
            target_role="Platform engineer",
        )

