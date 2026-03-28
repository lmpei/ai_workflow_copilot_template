from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import reset_database_for_tests
from app.models.document import DOCUMENT_STATUS_INDEXED
from app.repositories import document_repository, task_repository
from app.repositories.user_repository import create_user
from app.repositories.workspace_repository import create_workspace
from app.schemas.workspace import WorkspaceCreate
from app.services import support_case_service, task_execution_service
from app.services.retrieval_service import RetrievedChunk


@pytest.fixture(autouse=True)
def reset_database() -> None:
    reset_database_for_tests()


def _register_and_login(client: TestClient, *, email: str, name: str) -> dict[str, str]:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "super-secret",
            "name": name,
        },
    )
    assert register_response.status_code == 201
    user = register_response.json()

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "super-secret",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {
        "user_id": user["id"],
        "token": token,
    }


def _create_workspace(
    client: TestClient,
    token: str,
    *,
    name: str = "Support Demo",
    module_type: str = "support",
) -> str:
    response = client.post(
        "/api/v1/workspaces",
        json={"name": name, "module_type": module_type},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_completed_support_task(
    *,
    workspace_id: str,
    user_id: str,
    task_type: str = "reply_draft",
    input_json: dict[str, object] | None = None,
    result_json: dict[str, object] | None = None,
) -> str:
    task = task_repository.create_task(
        workspace_id=workspace_id,
        task_type=task_type,
        created_by=user_id,
        input_json=input_json
        or {
            "customer_issue": "Customer cannot reset password",
            "product_area": "Authentication",
            "severity": "high",
        },
    )
    running_task = task_repository.update_task_status(task.id, next_status="running")
    assert running_task is not None
    completed_task = task_repository.update_task_status(
        task.id,
        next_status="done",
        output_json={
            "result": result_json
            or {
                "module_type": "support",
                "task_type": task_type,
                "title": "Grounded Reply Draft",
                "summary": "Grounded password reset guidance was found for the case.",
                "input": {
                    "customer_issue": "Customer cannot reset password",
                    "product_area": "Authentication",
                    "severity": "high",
                },
                "case_brief": {
                    "issue_summary": "Customer cannot reset password",
                    "product_area": "Authentication",
                    "severity": "high",
                    "evidence_status": "grounded_matches",
                    "reproduction_steps": [],
                },
                "findings": [
                    {
                        "title": "Reset guidance",
                        "summary": "Password reset links expire after 15 minutes.",
                        "evidence_ref_ids": ["chunk-1"],
                    }
                ],
                "triage": {
                    "evidence_status": "grounded_matches",
                    "needs_manual_review": True,
                    "should_escalate": True,
                    "recommended_owner": "support_escalation",
                    "rationale": "Human review is required before updating the customer.",
                },
                "open_questions": ["Was the link older than 15 minutes?"],
                "next_steps": ["Confirm whether a new reset link should be issued."],
                "reply_draft": {
                    "subject_line": "Support update for your reported issue",
                    "body": "Reset links expire after 15 minutes.",
                    "confidence_note": "Grounded in indexed support knowledge.",
                },
                "escalation_packet": {
                    "recommended_owner": "support_escalation",
                    "needs_manual_review": True,
                    "should_escalate": True,
                    "evidence_status": "grounded_matches",
                    "escalation_reason": "Human review is required before updating the customer.",
                    "case_summary": "Grounded password reset guidance was found for the case.",
                    "findings": [],
                    "unresolved_questions": ["Was the link older than 15 minutes?"],
                    "recommended_next_steps": ["Confirm whether a new reset link should be issued."],
                    "evidence_ref_ids": ["chunk-1"],
                    "handoff_note": "Route this case to support_escalation.",
                },
                "highlights": ["Issue: Customer cannot reset password"],
                "evidence": [],
                "artifacts": {
                    "document_count": 1,
                    "match_count": 1,
                    "documents": [],
                    "matches": [],
                    "tool_call_ids": [],
                    "evidence_status": "grounded_matches",
                },
                "metadata": {},
            }
        },
    )
    assert completed_task is not None
    return task.id


def test_run_task_execution_syncs_support_case_metadata_and_creates_case(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeRetriever:
        def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
            assert workspace_id
            assert "Customer cannot reset password" in question
            return [
                RetrievedChunk(
                    document_id="doc-1",
                    chunk_id="chunk-1",
                    document_title="support-guide.md",
                    chunk_index=0,
                    snippet="Password reset links expire after 15 minutes.",
                    content="Password reset links expire after 15 minutes.",
                ),
            ]

    monkeypatch.setattr("app.agents.tool_registry.get_retriever", lambda: FakeRetriever())

    unique_suffix = uuid4().hex
    user = create_user(
        email=f"support-case-exec-{unique_suffix}@example.com",
        password_hash="not-used-in-this-test",
        name="Support Case Exec",
    )
    workspace = create_workspace(
        WorkspaceCreate(name="Support Case Workspace", module_type="support"),
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
    task = task_repository.create_task(
        workspace_id=workspace.id,
        task_type="reply_draft",
        created_by=user.id,
        input_json={
            "customer_issue": "Customer cannot reset password",
            "product_area": "Authentication",
            "severity": "high",
        },
    )

    output = task_execution_service.run_task_execution(task.id)
    persisted_task = task_repository.get_task(task.id)
    assert persisted_task is not None

    support_case_link = output["result"]["metadata"]["support_case"]
    assert isinstance(support_case_link, dict)
    assert support_case_link["case_status"] == "escalated"

    support_cases = support_case_service.list_workspace_support_cases(
        workspace_id=workspace.id,
        user_id=user.id,
    )
    assert len(support_cases) == 1
    assert support_cases[0].id == support_case_link["case_id"]
    assert support_cases[0].event_count == 1
    assert support_cases[0].latest_task_id == task.id
    assert support_cases[0].action_loop.can_continue is True
    assert support_cases[0].action_loop.continue_from_task_id == task.id
    assert support_cases[0].action_loop.suggested_task_type == "ticket_summary"

    support_case = support_case_service.get_support_case(
        case_id=support_cases[0].id,
        user_id=user.id,
    )
    assert support_case is not None
    assert len(support_case.events) == 1
    assert support_case.events[0].task_id == task.id
    assert support_case.action_loop.can_continue is True
    assert support_case.action_loop.continue_from_task_id == task.id
    assert persisted_task.output_json["result"]["metadata"]["support_case"]["case_id"] == support_case.id


def test_support_case_routes_list_and_get_follow_up_case(client: TestClient) -> None:
    auth = _register_and_login(client, email="support-case-owner@example.com", name="Support Case Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"], module_type="support")

    parent_task_id = _create_completed_support_task(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
    )
    parent_task = task_repository.get_task(parent_task_id)
    assert parent_task is not None
    parent_result = parent_task.output_json["result"]
    support_case_service.sync_support_case_from_task(task=parent_task, result_json=parent_result)

    follow_up_task_id = _create_completed_support_task(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        input_json={
            "customer_issue": "Customer cannot reset password",
            "product_area": "Authentication",
            "severity": "high",
            "parent_task_id": parent_task_id,
            "follow_up_notes": "Customer says the reset link failed twice.",
        },
        result_json={
            "module_type": "support",
            "task_type": "reply_draft",
            "title": "Grounded Reply Draft",
            "summary": "Follow-up review confirmed the case still needs escalation.",
            "input": {
                "customer_issue": "Customer cannot reset password",
                "product_area": "Authentication",
                "severity": "high",
                "parent_task_id": parent_task_id,
                "follow_up_notes": "Customer says the reset link failed twice.",
            },
            "lineage": {
                "parent_task_id": parent_task_id,
                "parent_task_type": "reply_draft",
                "parent_title": "Grounded Reply Draft",
                "parent_summary": "Grounded password reset guidance was found for the case.",
                "parent_customer_issue": "Customer cannot reset password",
                "parent_product_area": "Authentication",
                "parent_severity": "high",
                "parent_reproduction_steps": [],
                "parent_recommended_owner": "support_escalation",
                "parent_evidence_status": "grounded_matches",
                "follow_up_notes": "Customer says the reset link failed twice.",
            },
            "case_brief": {
                "issue_summary": "Customer cannot reset password",
                "product_area": "Authentication",
                "severity": "high",
                "evidence_status": "grounded_matches",
                "reproduction_steps": [],
            },
            "findings": [],
            "triage": {
                "evidence_status": "grounded_matches",
                "needs_manual_review": True,
                "should_escalate": True,
                "recommended_owner": "support_escalation",
                "rationale": "The case still requires manual escalation.",
            },
            "open_questions": ["Should support manually reissue the reset flow?"],
            "next_steps": ["Continue with manual escalation."],
            "reply_draft": {
                "subject_line": "Support update for your reported issue",
                "body": "We are escalating the case for manual review.",
                "confidence_note": "Grounded in indexed support knowledge.",
            },
            "escalation_packet": {
                "recommended_owner": "support_escalation",
                "needs_manual_review": True,
                "should_escalate": True,
                "evidence_status": "grounded_matches",
                "escalation_reason": "The case still requires manual escalation.",
                "case_summary": "Follow-up review confirmed the case still needs escalation.",
                "findings": [],
                "unresolved_questions": ["Should support manually reissue the reset flow?"],
                "recommended_next_steps": ["Continue with manual escalation."],
                "evidence_ref_ids": ["chunk-1"],
                "follow_up_notes": "Customer says the reset link failed twice.",
                "handoff_note": "Route this case to support_escalation.",
            },
            "highlights": ["Issue: Customer cannot reset password"],
            "evidence": [],
            "artifacts": {
                "document_count": 1,
                "match_count": 1,
                "documents": [],
                "matches": [],
                "tool_call_ids": [],
                "evidence_status": "grounded_matches",
            },
            "metadata": {},
        },
    )
    follow_up_task = task_repository.get_task(follow_up_task_id)
    assert follow_up_task is not None
    follow_up_result = follow_up_task.output_json["result"]
    metadata = support_case_service.sync_support_case_from_task(task=follow_up_task, result_json=follow_up_result)
    case_id = metadata["support_case"]["case_id"]

    list_response = client.get(
        f"/api/v1/workspaces/{workspace_id}/support-cases",
        headers=headers,
    )
    assert list_response.status_code == 200
    listed_cases = list_response.json()
    assert len(listed_cases) == 1
    assert listed_cases[0]["id"] == case_id
    assert listed_cases[0]["event_count"] == 2
    assert listed_cases[0]["latest_task_id"] == follow_up_task_id
    assert listed_cases[0]["action_loop"]["can_continue"] is True
    assert listed_cases[0]["action_loop"]["continue_from_task_id"] == follow_up_task_id
    assert listed_cases[0]["action_loop"]["suggested_task_type"] == "ticket_summary"

    detail_response = client.get(f"/api/v1/support-cases/{case_id}", headers=headers)
    assert detail_response.status_code == 200
    support_case = detail_response.json()
    assert support_case["id"] == case_id
    assert support_case["status"] == "escalated"
    assert support_case["latest_summary"] == "Follow-up review confirmed the case still needs escalation."
    assert support_case["action_loop"]["can_continue"] is True
    assert support_case["action_loop"]["continue_from_task_id"] == follow_up_task_id
    assert support_case["action_loop"]["suggested_task_type"] == "ticket_summary"
    assert len(support_case["events"]) == 2
    assert support_case["events"][0]["task_id"] == follow_up_task_id
    assert support_case["events"][0]["event_kind"] == "follow_up"
