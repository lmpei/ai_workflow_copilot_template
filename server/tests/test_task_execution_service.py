import asyncio
from uuid import uuid4

import pytest

from app.core.database import reset_database_for_tests
from app.core.runtime_control import build_cancel_requested_control
from app.models.document import DOCUMENT_STATUS_INDEXED
from app.repositories import document_repository, research_asset_repository, task_repository, trace_repository
from app.repositories.user_repository import create_user
from app.repositories.workspace_repository import create_workspace
from app.schemas.research_asset import ResearchAssetCreate
from app.schemas.workspace import WorkspaceCreate
from app.services import research_asset_service, task_execution_service
from app.services.agent_service import AgentExecutionResult
from app.services.retrieval_service import RetrievedChunk
from app.services.task_execution_service import TaskExecutionError
from app.workers.task_worker import run_platform_task


class FakeJob:
    def __init__(self, job_id: str) -> None:
        self.job_id = job_id


class FakePool:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.closed = False

    async def enqueue_job(self, function_name: str, task_id: str, _queue_name: str) -> FakeJob:
        self.calls.append(
            {
                "function_name": function_name,
                "task_id": task_id,
                "queue_name": _queue_name,
            },
        )
        return FakeJob("job-123")

    async def aclose(self) -> None:
        self.closed = True


@pytest.fixture(autouse=True)
def reset_database() -> None:
    reset_database_for_tests()



def _create_task_fixture(
    *,
    task_type: str = "research_summary",
    goal: str | None = None,
    with_document: bool = True,
    workspace_type: str = "research",
    input_json: dict[str, object] | None = None,
) -> str:
    unique_suffix = uuid4().hex
    user = create_user(
        email=f"phase3-worker-{unique_suffix}@example.com",
        password_hash="not-used-in-this-test",
        name="Phase 3 Worker",
    )
    workspace = create_workspace(
        WorkspaceCreate(name="Phase 3 Worker Workspace", module_type=workspace_type),
        owner_id=user.id,
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
    task = task_repository.create_task(
        workspace_id=workspace.id,
        task_type=task_type,
        created_by=user.id,
        input_json=(
            input_json
            if input_json is not None
            else ({"goal": goal} if goal is not None else {})
        ),
    )
    return task.id


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



def test_enqueue_task_execution_uses_arq_pool(monkeypatch: pytest.MonkeyPatch) -> None:
    task_id = _create_task_fixture()
    fake_pool = FakePool()

    async def fake_create_pool(_settings: object) -> FakePool:
        return fake_pool

    monkeypatch.setattr(task_execution_service, "create_pool", fake_create_pool)
    monkeypatch.setattr(task_execution_service, "build_redis_settings", lambda: object())

    job_id = asyncio.run(task_execution_service.enqueue_task_execution(task_id))

    assert job_id == "job-123"
    assert fake_pool.calls == [
        {
            "function_name": task_execution_service.TASK_EXECUTION_JOB_NAME,
            "task_id": task_id,
            "queue_name": "platform_tasks",
        },
    ]
    assert fake_pool.closed is True



def test_run_task_execution_executes_research_summary_and_persists_output(
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

    task_id = _create_task_fixture(goal="Who owns the project?")

    output = task_execution_service.run_task_execution(task_id)
    persisted_task = task_repository.get_task(task_id)

    assert output["worker"] == "arq"
    assert output["task_type"] == "research_summary"
    assert output["agent_name"] == "workspace_research_agent"
    assert output["result"]["module_type"] == "research"
    assert output["result"]["task_type"] == "research_summary"
    assert output["result"]["input"]["goal"] == "Who owns the project?"
    assert output["result"]["input"]["deliverable"] == "brief"
    assert output["result"]["sections"]["findings"][0]["evidence_ref_ids"] == ["chunk-1"]
    assert output["result"]["artifacts"]["matches"][0]["document_title"] == "demo.txt"
    assert output["result"]["evidence"][0]["metadata"]["document_id"] == "doc-1"
    assert output["trace_id"]
    assert persisted_task is not None
    assert persisted_task.status == "done"
    assert persisted_task.output_json == {key: value for key, value in output.items() if key not in {"control_json", "recovery_state"}}

    agent_runs = task_repository.list_task_agent_runs(task_id)
    assert len(agent_runs) == 1
    assert agent_runs[0].status == "completed"

    tool_calls = task_repository.list_agent_run_tool_calls(agent_runs[0].id)
    assert [tool_call.tool_name for tool_call in tool_calls] == [
        "list_workspace_documents",
        "search_documents",
    ]
    assert all(tool_call.status == "completed" for tool_call in tool_calls)

    traces = trace_repository.list_traces_for_task(task_id)
    assert len(traces) == 1
    assert traces[0].trace_type == "research_task"
    assert traces[0].request_json["prompt"] == "Who owns the project?"
    assert traces[0].response_json["status"] == "completed"
    assert traces[0].response_json["regression_passed"] is True
    assert traces[0].metadata_json["regression_passed"] is True
    assert traces[0].metadata_json["regression_baseline"]["baseline_version"] == "stage_a_research_regression_v1"
    assert traces[0].metadata_json["trust"]["regression_passed"] is True



def test_run_task_execution_completes_workspace_report_with_limited_context() -> None:
    task_id = _create_task_fixture(
        task_type="workspace_report",
        goal=None,
        with_document=False,
    )

    output = task_execution_service.run_task_execution(task_id)
    persisted_task = task_repository.get_task(task_id)

    assert output["task_type"] == "workspace_report"
    assert output["result"]["title"] == "Workspace Report"
    assert output["result"]["input"]["deliverable"] == "report"
    assert "open_questions" in output["result"]["sections"]
    assert output["result"]["report"]["headline"] == "Research Report: Workspace research report"
    assert output["result"]["report"]["sections"][0]["slug"] == "findings"
    assert output["result"]["report"]["open_questions"][0].startswith("What source documents")
    assert output["result"]["metadata"]["report_ready"] is True
    assert output["result"]["artifacts"]["document_count"] == 0
    assert output["result"]["artifacts"]["matches"] == []
    assert output["result"]["summary"] == "No workspace documents are available for analysis."
    assert output["result"]["metadata"]["regression_passed"] is False
    assert output["trace_id"]
    assert persisted_task is not None
    assert persisted_task.status == "done"

    agent_runs = task_repository.list_task_agent_runs(task_id)
    assert len(agent_runs) == 1
    tool_calls = task_repository.list_agent_run_tool_calls(agent_runs[0].id)
    assert [tool_call.tool_name for tool_call in tool_calls] == ["list_workspace_documents"]

    traces = trace_repository.list_traces_for_task(task_id)
    assert len(traces) == 1
    assert traces[0].response_json["evidence_status"] == "no_documents"
    assert traces[0].response_json["regression_passed"] is False
    assert "no_documents_available" in traces[0].metadata_json["regression_baseline"]["issues"]
    assert traces[0].metadata_json["trust"]["gaps"] == ["no_documents_available"]



def test_run_task_execution_persists_formal_workspace_report_with_evidence(
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
                    snippet="Delayed sign-off is the strongest grounded delivery risk.",
                    content="Delayed sign-off is the strongest grounded delivery risk.",
                ),
            ]

    monkeypatch.setattr("app.agents.tool_registry.get_retriever", lambda: FakeRetriever())

    task_id = _create_task_fixture(
        task_type="workspace_report",
        input_json={
            "goal": "Build a grounded workspace report",
            "deliverable": "report",
            "key_questions": ["What slipped?", "What needs more support?"],
        },
    )

    output = task_execution_service.run_task_execution(task_id)
    persisted_task = task_repository.get_task(task_id)

    assert output["task_type"] == "workspace_report"
    assert output["result"]["report"]["headline"] == "Research Report: Build a grounded workspace report"
    assert output["result"]["report"]["sections"][0]["slug"] == "findings"
    assert output["result"]["report"]["sections"][0]["evidence_ref_ids"] == ["chunk-1"]
    assert output["result"]["report"]["evidence_ref_ids"] == ["chunk-1"]
    assert output["result"]["metadata"]["report_ready"] is True
    assert persisted_task is not None
    assert persisted_task.status == "done"
    assert persisted_task.output_json == {key: value for key, value in output.items() if key not in {"control_json", "recovery_state"}}

    agent_runs = task_repository.list_task_agent_runs(task_id)
    assert len(agent_runs) == 1
    tool_calls = task_repository.list_agent_run_tool_calls(agent_runs[0].id)
    assert [tool_call.tool_name for tool_call in tool_calls] == [
        "list_workspace_documents",
        "search_documents",
    ]


def test_run_task_execution_carries_follow_up_research_lineage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeRetriever:
        def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
            assert workspace_id
            assert "Continue the prior research run" in question
            assert "Prior summary: Delayed sign-off is the strongest current risk." in question
            assert "Follow-up guidance: Focus on unresolved evidence gaps." in question
            return [
                RetrievedChunk(
                    document_id="doc-1",
                    chunk_id="chunk-1",
                    document_title="demo.txt",
                    chunk_index=0,
                    snippet="Delayed sign-off still lacks owner-level evidence.",
                    content="Delayed sign-off still lacks owner-level evidence.",
                ),
            ]

    monkeypatch.setattr("app.agents.tool_registry.get_retriever", lambda: FakeRetriever())

    unique_suffix = uuid4().hex
    user = create_user(
        email=f"follow-up-worker-{unique_suffix}@example.com",
        password_hash="not-used-in-this-test",
        name="Follow-up Worker",
    )
    workspace = create_workspace(
        WorkspaceCreate(name="Follow-up Research Workspace", module_type="research"),
        owner_id=user.id,
    )
    document_repository.create_document(
        document_id=str(uuid4()),
        workspace_id=workspace.id,
        title="demo.txt",
        file_path="uploads/demo.txt",
        mime_type="text/plain",
        created_by=user.id,
        status=DOCUMENT_STATUS_INDEXED,
    )
    parent_task = task_repository.create_task(
        workspace_id=workspace.id,
        task_type="workspace_report",
        created_by=user.id,
        input_json={
            "goal": "Build a grounded workspace report",
            "deliverable": "report",
        },
    )
    parent_output = {
        "result": {
            "module_type": "research",
            "task_type": "workspace_report",
            "title": "Workspace Report",
            "summary": "Delayed sign-off is the strongest current risk.",
            "input": {"goal": "Build a grounded workspace report"},
            "report": {"headline": "Research Report: Build a grounded workspace report"},
            "sections": {
                "summary": "Delayed sign-off is the strongest current risk.",
                "findings": [],
                "evidence_overview": [],
                "open_questions": [],
                "next_steps": [],
            },
            "highlights": [],
            "evidence": [],
            "artifacts": {
                "document_count": 1,
                "match_count": 1,
                "documents": [],
                "matches": [],
                "tool_call_ids": [],
            },
            "metadata": {},
        },
    }
    running_parent = task_repository.update_task_status(
        parent_task.id,
        next_status="running",
    )
    assert running_parent is not None
    updated_parent = task_repository.update_task_status(
        parent_task.id,
        next_status="done",
        output_json=parent_output,
    )

    assert updated_parent is not None
    follow_up_task = task_repository.create_task(
        workspace_id=workspace.id,
        task_type="workspace_report",
        created_by=user.id,
        input_json={
            "goal": "Refine the strongest risk",
            "deliverable": "report",
            "parent_task_id": parent_task.id,
            "continuation_notes": "Focus on unresolved evidence gaps.",
        },
    )
    output = task_execution_service.run_task_execution(follow_up_task.id)
    traces = trace_repository.list_traces_for_task(follow_up_task.id)

    assert output["result"]["lineage"]["parent_task_id"] == parent_task.id
    assert output["result"]["lineage"]["parent_summary"] == "Delayed sign-off is the strongest current risk."
    assert output["result"]["metadata"]["is_follow_up"] is True
    assert output["result"]["metadata"]["parent_task_id"] == parent_task.id
    assert output["result"]["report"]["headline"] == "Research Follow-up Report: Refine the strongest risk"
    assert traces[0].request_json["lineage"]["parent_task_id"] == parent_task.id
    assert traces[0].metadata_json["is_follow_up"] is True
    assert traces[0].metadata_json["regression_baseline"]["signals"]["is_follow_up"] is True


def test_run_task_execution_appends_research_asset_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeRetriever:
        def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
            assert workspace_id
            assert "Continue the prior research run" in question
            return [
                RetrievedChunk(
                    document_id="doc-1",
                    chunk_id="chunk-2",
                    document_title="demo.txt",
                    chunk_index=1,
                    snippet="Ownership evidence is still missing from the escalation notes.",
                    content="Ownership evidence is still missing from the escalation notes.",
                ),
            ]

    monkeypatch.setattr("app.agents.tool_registry.get_retriever", lambda: FakeRetriever())

    unique_suffix = uuid4().hex
    user = create_user(
        email=f"research-asset-worker-{unique_suffix}@example.com",
        password_hash="not-used-in-this-test",
        name="Research Asset Worker",
    )
    workspace = create_workspace(
        WorkspaceCreate(name="Research Asset Workspace", module_type="research"),
        owner_id=user.id,
    )
    document_repository.create_document(
        document_id=str(uuid4()),
        workspace_id=workspace.id,
        title="demo.txt",
        file_path="uploads/demo.txt",
        mime_type="text/plain",
        created_by=user.id,
        status=DOCUMENT_STATUS_INDEXED,
    )
    parent_task = task_repository.create_task(
        workspace_id=workspace.id,
        task_type="workspace_report",
        created_by=user.id,
        input_json={
            "goal": "Build a grounded workspace report",
            "deliverable": "report",
        },
    )
    running_parent = task_repository.update_task_status(parent_task.id, next_status="running")
    assert running_parent is not None
    completed_parent = task_repository.update_task_status(
        parent_task.id,
        next_status="done",
        output_json={
            "result": {
                "module_type": "research",
                "task_type": "workspace_report",
                "title": "Workspace Report",
                "summary": "Delayed sign-off is the strongest current risk.",
                "input": {"goal": "Build a grounded workspace report", "deliverable": "report"},
                "report": {"headline": "Research Report: Build a grounded workspace report"},
                "sections": {
                    "summary": "Delayed sign-off is the strongest current risk.",
                    "findings": [],
                    "evidence_overview": [],
                    "open_questions": ["Who owns the unresolved sign-off gap?"],
                    "next_steps": [],
                },
                "highlights": [],
                "evidence": [],
                "artifacts": {
                    "document_count": 1,
                    "match_count": 1,
                    "documents": [],
                    "matches": [],
                    "tool_call_ids": [],
                },
                "metadata": {},
            },
        },
    )
    assert completed_parent is not None

    asset = research_asset_service.create_research_asset_from_task(
        workspace_id=workspace.id,
        user_id=user.id,
        payload=ResearchAssetCreate(task_id=parent_task.id),
    )

    follow_up_task = task_repository.create_task(
        workspace_id=workspace.id,
        task_type="workspace_report",
        created_by=user.id,
        input_json={
            "goal": "Refine the strongest risk",
            "deliverable": "report",
            "research_asset_id": asset.id,
            "parent_task_id": parent_task.id,
            "continuation_notes": "Confirm who owns the sign-off gap.",
        },
    )

    output = task_execution_service.run_task_execution(follow_up_task.id)
    persisted_task = task_repository.get_task(follow_up_task.id)
    persisted_asset = research_asset_repository.get_research_asset(asset.id)
    revisions = research_asset_repository.list_research_asset_revisions(asset.id)

    assert output["result"]["metadata"]["research_asset"]["asset_id"] == asset.id
    assert output["result"]["metadata"]["research_asset"]["revision_number"] == 2
    assert persisted_task is not None
    assert persisted_task.output_json == {key: value for key, value in output.items() if key not in {"control_json", "recovery_state"}}
    assert persisted_asset is not None
    assert persisted_asset.latest_task_id == follow_up_task.id
    assert persisted_asset.latest_revision_number == 2
    assert revisions[0].task_id == follow_up_task.id
    assert revisions[0].revision_number == 2
    assert revisions[1].task_id == parent_task.id


def test_run_task_execution_executes_support_reply_draft_and_persists_output(
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

    task_id = _create_task_fixture(
        task_type="reply_draft",
        workspace_type="support",
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

    output = task_execution_service.run_task_execution(task_id)
    persisted_task = task_repository.get_task(task_id)

    assert output["task_type"] == "reply_draft"
    assert output["agent_name"] == "workspace_support_agent"
    assert output["result"]["module_type"] == "support"
    assert output["result"]["task_type"] == "reply_draft"
    assert output["result"]["input"]["product_area"] == "Authentication"
    assert output["result"]["case_brief"]["severity"] == "high"
    assert output["result"]["findings"][0]["evidence_ref_ids"] == ["chunk-1"]
    assert output["result"]["reply_draft"]["subject_line"] == "Support update for your reported issue"
    assert output["result"]["triage"]["recommended_owner"] == "support_escalation"
    assert output["result"]["artifacts"]["match_count"] == 1
    assert output["result"]["artifacts"]["evidence_status"] == "grounded_matches"
    assert persisted_task is not None
    assert persisted_task.status == "done"



def test_run_task_execution_carries_support_follow_up_lineage_and_escalation_packet(
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
        email=f"support-follow-up-worker-{unique_suffix}@example.com",
        password_hash="not-used-in-this-test",
        name="Support Follow Up Worker",
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

    output = task_execution_service.run_task_execution(follow_up_task.id)
    persisted_task = task_repository.get_task(follow_up_task.id)

    assert output["result"]["lineage"]["parent_task_id"] == parent_task.id
    assert output["result"]["input"]["customer_issue"] == "Customer cannot reset their password"
    assert output["result"]["metadata"]["is_follow_up"] is True
    assert output["result"]["metadata"]["parent_task_id"] == parent_task.id
    assert output["result"]["reply_draft"]["body"].startswith("We continued review")
    assert output["result"]["escalation_packet"]["follow_up_notes"] == "Confirm whether the reset link can be reissued safely."
    assert output["result"]["escalation_packet"]["evidence_status"] == "grounded_matches"
    assert persisted_task is not None
    assert persisted_task.status == "done"


def test_run_task_execution_completes_support_ticket_summary_with_limited_context() -> None:
    task_id = _create_task_fixture(
        task_type="ticket_summary",
        workspace_type="support",
        with_document=False,
        input_json={
            "customer_issue": "Customer billing question",
            "desired_outcome": "Confirm next billing step",
        },
    )

    output = task_execution_service.run_task_execution(task_id)
    persisted_task = task_repository.get_task(task_id)

    assert output["task_type"] == "ticket_summary"
    assert output["result"]["title"] == "Support Ticket Summary"
    assert output["result"]["case_brief"]["desired_outcome"] == "Confirm next billing step"
    assert output["result"]["triage"]["recommended_owner"] == "knowledge_base_owner"
    assert output["result"]["open_questions"][0] == "Which product area or feature is affected?"
    assert output["result"]["next_steps"][0].startswith("Index support runbooks")
    assert output["result"]["artifacts"]["document_count"] == 0
    assert output["result"]["artifacts"]["matches"] == []
    assert output["result"]["artifacts"]["evidence_status"] == "no_documents"
    assert output["result"]["escalation_packet"]["evidence_status"] == "no_documents"
    assert output["result"]["escalation_packet"]["should_escalate"] is True
    assert "No indexed support knowledge was available" in output["result"]["escalation_packet"]["handoff_note"]
    assert (
        output["result"]["summary"]
        == "No support knowledge documents are available for this workspace."
    )
    assert persisted_task is not None
    assert persisted_task.status == "done"


def test_run_task_execution_executes_job_resume_match_and_persists_output(
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

    task_id = _create_task_fixture(
        task_type="resume_match",
        workspace_type="job",
        input_json={
            "target_role": "Platform engineer",
            "seniority": "senior",
            "must_have_skills": ["Python", "API design"],
            "preferred_skills": ["Reliability"],
            "hiring_context": "Core platform modernization",
        },
    )

    output = task_execution_service.run_task_execution(task_id)
    persisted_task = task_repository.get_task(task_id)

    assert output["task_type"] == "resume_match"
    assert output["agent_name"] == "workspace_job_agent"
    assert output["result"]["module_type"] == "job"
    assert output["result"]["input"]["seniority"] == "senior"
    assert output["result"]["review_brief"]["must_have_skills"] == ["Python", "API design"]
    assert output["result"]["findings"][0]["evidence_ref_ids"] == ["chunk-1"]
    assert output["result"]["assessment"]["recommended_outcome"] == "advance_to_manual_review"
    assert output["result"]["artifacts"]["fit_signal"] == "grounded_match_found"
    assert output["result"]["artifacts"]["evidence_status"] == "grounded_matches"
    assert persisted_task is not None
    assert persisted_task.status == "done"


def test_run_task_execution_completes_job_jd_summary_with_limited_context() -> None:
    task_id = _create_task_fixture(
        task_type="jd_summary",
        workspace_type="job",
        with_document=False,
        input_json={
            "target_role": "Platform engineer",
            "seniority": "mid",
        },
    )

    output = task_execution_service.run_task_execution(task_id)
    persisted_task = task_repository.get_task(task_id)

    assert output["task_type"] == "jd_summary"
    assert output["result"]["title"] == "Job Description Summary"
    assert output["result"]["review_brief"]["seniority"] == "mid"
    assert output["result"]["assessment"]["recommended_outcome"] == "gather_hiring_materials"
    assert output["result"]["gaps"][0] == "Must-have skills are not specified."
    assert output["result"]["artifacts"]["document_count"] == 0
    assert output["result"]["artifacts"]["fit_signal"] == "no_documents_available"
    assert output["result"]["artifacts"]["evidence_status"] == "no_documents"
    assert output["result"]["summary"] == "No job documents are available for this workspace."
    assert persisted_task is not None
    assert persisted_task.status == "done"


def test_run_task_execution_builds_job_shortlist_from_completed_candidate_reviews(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeRetriever:
        def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
            assert workspace_id
            assert "Compare these completed candidate reviews for the same hiring decision." in question
            assert "Candidate A: Strong backend ownership with grounded platform evidence." in question
            assert "Candidate B: Candidate materials are still missing for a grounded decision." in question
            return [
                RetrievedChunk(
                    document_id="doc-1",
                    chunk_id="chunk-1",
                    document_title="hiring-plan.md",
                    chunk_index=0,
                    snippet="Backend ownership matters more than breadth for this role.",
                    content="Backend ownership matters more than breadth for this role.",
                ),
            ]

    monkeypatch.setattr("app.agents.tool_registry.get_retriever", lambda: FakeRetriever())

    unique_suffix = uuid4().hex
    user = create_user(
        email=f"job-shortlist-worker-{unique_suffix}@example.com",
        password_hash="not-used-in-this-test",
        name="Job Shortlist Worker",
    )
    workspace = create_workspace(
        WorkspaceCreate(name="Job Shortlist Workspace", module_type="job"),
        owner_id=user.id,
    )
    document_repository.create_document(
        document_id=str(uuid4()),
        workspace_id=workspace.id,
        title="hiring-plan.md",
        file_path="uploads/hiring-plan.md",
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
        summary="Candidate materials are still missing for a grounded decision.",
        fit_signal="no_documents_available",
        evidence_status="no_documents",
        recommended_outcome="gather_hiring_materials",
    )
    shortlist_task = task_repository.create_task(
        workspace_id=workspace.id,
        task_type="resume_match",
        created_by=user.id,
        input_json={
            "target_role": "Platform engineer",
            "comparison_task_ids": [candidate_a_task_id, candidate_b_task_id],
            "comparison_notes": "Prioritize backend ownership and highlight missing evidence.",
        },
    )

    output = task_execution_service.run_task_execution(shortlist_task.id)
    persisted_task = task_repository.get_task(shortlist_task.id)

    assert output["result"]["title"] == "Candidate Comparison Shortlist"
    assert output["result"]["comparison_candidates"][0]["candidate_label"] == "Candidate A"
    assert output["result"]["shortlist"]["entries"][0]["candidate_label"] == "Candidate A"
    assert output["result"]["shortlist"]["entries"][1]["candidate_label"] == "Candidate B"
    assert (
        "Some candidate reviews still lack indexed supporting materials."
        in output["result"]["shortlist"]["gaps"]
    )
    assert output["result"]["metadata"]["shortlist_ready"] is True
    assert persisted_task is not None
    assert persisted_task.status == "done"



def test_run_task_execution_marks_task_failed_when_agent_execution_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingRetriever:
        def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
            raise RuntimeError("Chroma unavailable")

    monkeypatch.setattr("app.agents.tool_registry.get_retriever", lambda: FailingRetriever())

    task_id = _create_task_fixture(goal="Who owns the project?")

    with pytest.raises(TaskExecutionError, match="Task execution failed"):
        task_execution_service.run_task_execution(task_id)

    persisted_task = task_repository.get_task(task_id)
    assert persisted_task is not None
    assert persisted_task.status == "failed"
    assert persisted_task.error_message == "Chroma unavailable"
    assert persisted_task.output_json["error"]["type"] == "agent_runtime_error"
    assert persisted_task.output_json["trace_id"]

    agent_runs = task_repository.list_task_agent_runs(task_id)
    assert len(agent_runs) == 1
    assert agent_runs[0].status == "failed"

    traces = trace_repository.list_traces_for_task(task_id)
    assert len(traces) == 1
    assert traces[0].trace_type == "research_task"
    assert traces[0].error_message == "Chroma unavailable"
    assert traces[0].metadata_json["failure"]["type"] == "agent_runtime_error"



def test_run_task_execution_rejects_invalid_module_task_combination() -> None:
    task_id = _create_task_fixture(goal="Who owns the project?", workspace_type="support")

    with pytest.raises(TaskExecutionError, match="Task type research_summary is not supported"):
        task_execution_service.run_task_execution(task_id)

    persisted_task = task_repository.get_task(task_id)
    assert persisted_task is not None
    assert persisted_task.status == "failed"
    assert persisted_task.output_json["error"]["type"] == "contract_error"



def test_run_task_execution_rejects_invalid_support_module_task_combination() -> None:
    task_id = _create_task_fixture(
        task_type="ticket_summary",
        workspace_type="research",
        input_json={"customer_issue": "Customer billing question"},
    )

    with pytest.raises(TaskExecutionError, match="Task type ticket_summary is not supported"):
        task_execution_service.run_task_execution(task_id)

    persisted_task = task_repository.get_task(task_id)
    assert persisted_task is not None
    assert persisted_task.status == "failed"


def test_run_task_execution_rejects_invalid_job_module_task_combination() -> None:
    task_id = _create_task_fixture(
        task_type="jd_summary",
        workspace_type="support",
        input_json={"target_role": "Platform engineer"},
    )

    with pytest.raises(TaskExecutionError, match="Task type jd_summary is not supported"):
        task_execution_service.run_task_execution(task_id)

    persisted_task = task_repository.get_task(task_id)
    assert persisted_task is not None
    assert persisted_task.status == "failed"



def test_run_task_execution_short_circuits_running_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_id = _create_task_fixture(goal="Who owns the project?")
    running_task = task_repository.update_task_status(task_id, next_status="running")

    assert running_task is not None
    monkeypatch.setattr(
        task_execution_service,
        "_execute_task_agent",
        lambda _task: pytest.fail("running tasks should not execute again"),
    )

    output = task_execution_service.run_task_execution(task_id)
    persisted_task = task_repository.get_task(task_id)

    assert output == {
        "task_id": task_id,
        "task_type": "research_summary",
        "worker": "arq",
        "status": "running",
        "skipped": True,
        "control_json": {},
        "recovery_state": "running",
    }
    assert persisted_task is not None
    assert persisted_task.status == "running"
    assert task_repository.list_task_agent_runs(task_id) == []


def test_run_task_execution_returns_existing_output_for_completed_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_id = _create_task_fixture(goal="Who owns the project?")
    running_task = task_repository.update_task_status(task_id, next_status="running")

    assert running_task is not None
    expected_output = {
        "task_id": task_id,
        "task_type": "research_summary",
        "worker": "arq",
        "status": "completed",
        "agent_name": "workspace_research_agent",
        "agent_run_id": "agent-run-1",
        "result": {"module_type": "research"},
    }
    completed_task = task_repository.update_task_status(
        task_id,
        next_status="done",
        output_json=expected_output,
    )

    assert completed_task is not None
    monkeypatch.setattr(
        task_execution_service,
        "_execute_task_agent",
        lambda _task: pytest.fail("completed tasks should not execute again"),
    )

    output = task_execution_service.run_task_execution(task_id)

    assert output == {
        **expected_output,
        "control_json": {},
        "recovery_state": "done",
    }
    assert task_repository.list_task_agent_runs(task_id) == []


def test_run_task_execution_short_circuits_failed_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_id = _create_task_fixture(goal="Who owns the project?")
    failed_task = task_repository.update_task_status(
        task_id,
        next_status="failed",
        error_message="Previous worker failure",
    )

    assert failed_task is not None
    monkeypatch.setattr(
        task_execution_service,
        "_execute_task_agent",
        lambda _task: pytest.fail("failed tasks should not execute again"),
    )

    output = task_execution_service.run_task_execution(task_id)
    persisted_task = task_repository.get_task(task_id)

    assert output == {
        "task_id": task_id,
        "task_type": "research_summary",
        "worker": "arq",
        "status": "failed",
        "skipped": True,
        "error_message": "Previous worker failure",
        "control_json": {},
        "recovery_state": "retryable_failed",
    }
    assert persisted_task is not None
    assert persisted_task.status == "failed"
    assert persisted_task.error_message == "Previous worker failure"
    assert task_repository.list_task_agent_runs(task_id) == []


def test_run_platform_task_worker_entrypoint_executes_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeRetriever:
        def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
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

    task_id = _create_task_fixture(goal="Who owns the project?")

    output = asyncio.run(run_platform_task({}, task_id))
    persisted_task = task_repository.get_task(task_id)

    assert output["task_id"] == task_id
    assert output["agent_name"] == "workspace_research_agent"
    assert output["result"]["module_type"] == "research"
    assert persisted_task is not None
    assert persisted_task.status == "done"

def test_run_task_execution_cancels_running_task_with_cancel_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_id = _create_task_fixture(goal="Who owns the project?")
    running_task = task_repository.update_task_status(
        task_id,
        next_status="running",
        control_json=build_cancel_requested_control(
            current_control_json={},
            user_id="operator-1",
            reason="Stop the stale retry.",
        ),
    )

    assert running_task is not None
    monkeypatch.setattr(
        task_execution_service,
        "_execute_task_agent",
        lambda _task: pytest.fail("cancel-requested running tasks should not execute again"),
    )

    output = task_execution_service.run_task_execution(task_id)
    persisted_task = task_repository.get_task(task_id)

    assert output["status"] == "failed"
    assert output["control_json"]["state"] == "cancelled"
    assert output["recovery_state"] == "cancelled"
    assert persisted_task is not None
    assert persisted_task.status == "failed"
    assert persisted_task.error_message == "Task cancelled by operator"
    assert persisted_task.control_json["state"] == "cancelled"


def test_run_task_execution_honors_cancel_request_recorded_during_agent_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_id = _create_task_fixture(goal="Who owns the project?")
    task = task_repository.get_task(task_id)
    assert task is not None

    def fake_execute(_task):
        task_repository.update_task_status(
            task_id,
            next_status="running",
            control_json=build_cancel_requested_control(
                current_control_json={},
                user_id=task.created_by,
                reason="Cancel after operator review.",
            ),
        )
        return AgentExecutionResult(
            agent_run_id="agent-run-cancelled",
            agent_name="workspace_research_agent",
            final_output={
                "module_type": "research",
                "task_type": "research_summary",
                "title": "Research Summary",
                "summary": "This result should not persist because the task was cancelled.",
                "sections": {
                    "summary": "This result should not persist because the task was cancelled.",
                    "findings": [],
                    "evidence_overview": [],
                    "open_questions": [],
                    "next_steps": [],
                },
                "highlights": [],
                "evidence": [],
                "artifacts": {
                    "document_count": 0,
                    "match_count": 0,
                    "documents": [],
                    "matches": [],
                    "tool_call_ids": [],
                },
                "metadata": {},
            },
        )

    monkeypatch.setattr(task_execution_service, "_execute_task_agent", fake_execute)

    output = task_execution_service.run_task_execution(task_id)
    persisted_task = task_repository.get_task(task_id)

    assert output["recovery_state"] == "cancelled"
    assert output["error_message"] == "Task cancelled by operator"
    assert persisted_task is not None
    assert persisted_task.status == "failed"
    assert persisted_task.control_json["state"] == "cancelled"
