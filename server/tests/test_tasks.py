from fastapi.testclient import TestClient

from app.repositories import task_repository
from app.services.task_execution_service import TaskExecutionError

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
    name: str = "Research Demo",
    workspace_type: str = "research",
) -> str:
    response = client.post(
        "/api/v1/workspaces",
        json={"name": name, "module_type": workspace_type},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    return response.json()["id"]


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



def test_task_routes_require_authentication(client: TestClient) -> None:
    post_response = client.post(
        "/api/v1/workspaces/demo-workspace/tasks",
        json={"task_type": "research_summary", "input": {}},
    )
    get_response = client.get("/api/v1/tasks/demo-task")
    list_response = client.get("/api/v1/workspaces/demo-workspace/tasks")

    assert post_response.status_code == 401
    assert get_response.status_code == 401
    assert list_response.status_code == 401



def test_create_get_and_list_tasks_for_workspace_member(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        fake_enqueue_task_execution,
    )

    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    create_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "research_summary",
            "input": {"goal": "Summarize indexed workspace findings"},
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    created_task = create_response.json()
    assert created_task["workspace_id"] == workspace_id
    assert created_task["task_type"] == "research_summary"
    assert created_task["status"] == "pending"
    assert created_task["input_json"] == {"goal": "Summarize indexed workspace findings"}
    assert created_task["output_json"] == {}

    get_response = client.get(f"/api/v1/tasks/{created_task['id']}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == created_task["id"]

    list_response = client.get(f"/api/v1/workspaces/{workspace_id}/tasks", headers=headers)
    assert list_response.status_code == 200
    listed_ids = [item["id"] for item in list_response.json()]
    assert listed_ids == [created_task["id"]]


def test_get_task_serializes_internal_done_status_as_completed(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        fake_enqueue_task_execution,
    )

    auth = _register_and_login(client, email="status-owner@example.com", name="Status Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    create_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "research_summary",
            "input": {"goal": "Summarize indexed workspace findings"},
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    created_task = create_response.json()

    running_task = task_repository.update_task_status(
        created_task["id"],
        next_status="running",
    )
    assert running_task is not None
    completed_task = task_repository.update_task_status(
        created_task["id"],
        next_status="done",
        control_json={
            "history": [
                {
                    "event": "completed",
                    "state": "done",
                    "at": "2026-03-22T00:00:00Z",
                }
            ]
        },
        output_json={"result": {"module_type": "research", "task_type": "research_summary"}},
    )
    assert completed_task is not None

    get_response = client.get(f"/api/v1/tasks/{created_task['id']}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "completed"
    assert get_response.json()["recovery_state"] == "completed"
    assert get_response.json()["recovery_detail"]["state"] == "completed"
    assert get_response.json()["recovery_detail"]["history"][-1]["state"] == "completed"



def test_create_research_task_accepts_structured_input_payload(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        fake_enqueue_task_execution,
    )

    auth = _register_and_login(client, email="structured-owner@example.com", name="Structured Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    create_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "workspace_report",
            "input": {
                "goal": "  Build a project brief  ",
                "focus_areas": [" Risks ", "Timeline", "Risks"],
                "key_questions": [" What slipped? ", "Who owns follow-up?"],
                "constraints": ["Use indexed docs only", "Use indexed docs only"],
                "deliverable": "report",
                "requested_sections": ["summary", "findings", "summary"],
            },
        },
        headers=headers,
    )

    assert create_response.status_code == 201
    created_task = create_response.json()
    assert created_task["input_json"] == {
        "goal": "Build a project brief",
        "focus_areas": ["Risks", "Timeline"],
        "key_questions": ["What slipped?", "Who owns follow-up?"],
        "constraints": ["Use indexed docs only"],
        "deliverable": "report",
        "requested_sections": ["summary", "findings"],
    }


def test_create_follow_up_research_task_accepts_completed_parent_task(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        fake_enqueue_task_execution,
    )

    auth = _register_and_login(client, email="follow-up-owner@example.com", name="Follow-up Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    parent_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "workspace_report",
            "input": {
                "goal": "Build the initial workspace report",
                "deliverable": "report",
            },
        },
        headers=headers,
    )
    assert parent_response.status_code == 201
    parent_task = parent_response.json()

    complete_parent_response = client.get(f"/api/v1/tasks/{parent_task['id']}", headers=headers)
    assert complete_parent_response.status_code == 200

    from app.repositories import task_repository

    running_parent = task_repository.update_task_status(
        parent_task["id"],
        next_status="running",
    )
    assert running_parent is not None
    updated_parent = task_repository.update_task_status(
        parent_task["id"],
        next_status="done",
        output_json={
            "result": {
                "module_type": "research",
                "task_type": "workspace_report",
                "title": "Workspace Report",
                "summary": "Delayed sign-off is the strongest current risk.",
                "input": {"goal": "Build the initial workspace report"},
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
                    "document_count": 0,
                    "match_count": 0,
                    "documents": [],
                    "matches": [],
                    "tool_call_ids": [],
                },
                "metadata": {},
            },
        },
    )
    assert updated_parent is not None

    follow_up_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "workspace_report",
            "input": {
                "goal": "Refine the strongest risk",
                "deliverable": "report",
                "parent_task_id": parent_task["id"],
                "continuation_notes": "Focus on evidence gaps that remain unresolved.",
            },
        },
        headers=headers,
    )

    assert follow_up_response.status_code == 201
    created_task = follow_up_response.json()
    assert created_task["input_json"]["parent_task_id"] == parent_task["id"]
    assert created_task["input_json"]["continuation_notes"] == "Focus on evidence gaps that remain unresolved."


def test_create_follow_up_research_task_rejects_incomplete_parent(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        fake_enqueue_task_execution,
    )

    auth = _register_and_login(client, email="follow-up-owner-2@example.com", name="Follow-up Owner 2")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    parent_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "research_summary",
            "input": {"goal": "Summarize the workspace"},
        },
        headers=headers,
    )
    assert parent_response.status_code == 201
    parent_task = parent_response.json()

    follow_up_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "workspace_report",
            "input": {
                "goal": "Refine the workspace report",
                "parent_task_id": parent_task["id"],
            },
        },
        headers=headers,
    )

    assert follow_up_response.status_code == 400
    assert "父级研究任务必须先完成后才能继续跟进" in follow_up_response.json()["detail"]


def test_create_support_task_for_support_workspace_member(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        fake_enqueue_task_execution,
    )

    auth = _register_and_login(client, email="support-owner@example.com", name="Support Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"], workspace_type="support")

    create_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "reply_draft",
            "input": {
                "customer_issue": "  Customer cannot reset their password  ",
                "product_area": " Authentication ",
                "severity": "high",
                "desired_outcome": " Restore access quickly ",
                "reproduction_steps": [
                    " Open reset email ",
                    "Click expired link",
                    "Open reset email",
                ],
            },
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    created_task = create_response.json()
    assert created_task["task_type"] == "reply_draft"
    assert created_task["status"] == "pending"
    assert created_task["input_json"] == {
        "customer_issue": "Customer cannot reset their password",
        "product_area": "Authentication",
        "severity": "high",
        "desired_outcome": "Restore access quickly",
        "reproduction_steps": [
            "Open reset email",
            "Click expired link",
        ],
    }


def test_create_follow_up_support_task_accepts_completed_parent_task(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        fake_enqueue_task_execution,
    )

    auth = _register_and_login(client, email="support-follow-up@example.com", name="Support Follow Up")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"], workspace_type="support")

    parent_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "reply_draft",
            "input": {
                "customer_issue": "Customer cannot reset their password",
                "product_area": "Authentication",
                "severity": "high",
            },
        },
        headers=headers,
    )
    assert parent_response.status_code == 201
    parent_task = parent_response.json()

    running_parent = task_repository.update_task_status(
        parent_task["id"],
        next_status="running",
    )
    assert running_parent is not None
    completed_parent = task_repository.update_task_status(
        parent_task["id"],
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
                "case_brief": {
                    "issue_summary": "Customer cannot reset their password",
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
                    "rationale": "Human review is required before updating the customer.",
                },
                "open_questions": [],
                "next_steps": [],
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
                    "unresolved_questions": [],
                    "recommended_next_steps": [],
                    "evidence_ref_ids": [],
                    "handoff_note": "Route this case to support_escalation.",
                },
                "highlights": [],
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
        },
    )
    assert completed_parent is not None

    follow_up_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "reply_draft",
            "input": {
                "parent_task_id": parent_task["id"],
                "follow_up_notes": "Confirm whether the reset link can be reissued safely.",
            },
        },
        headers=headers,
    )

    assert follow_up_response.status_code == 201
    created_task = follow_up_response.json()
    assert created_task["input_json"]["parent_task_id"] == parent_task["id"]
    assert created_task["input_json"]["follow_up_notes"] == "Confirm whether the reset link can be reissued safely."


def test_create_follow_up_support_task_rejects_incomplete_parent(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        fake_enqueue_task_execution,
    )

    auth = _register_and_login(client, email="support-follow-up-2@example.com", name="Support Follow Up 2")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"], workspace_type="support")

    parent_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "ticket_summary",
            "input": {"customer_issue": "Customer billing question"},
        },
        headers=headers,
    )
    assert parent_response.status_code == 201
    parent_task = parent_response.json()

    follow_up_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "reply_draft",
            "input": {
                "parent_task_id": parent_task["id"],
                "follow_up_notes": "Confirm who owns the next response.",
            },
        },
        headers=headers,
    )

    assert follow_up_response.status_code == 400
    assert "父级 Support 任务必须先完成后才能继续跟进" in follow_up_response.json()["detail"]


def test_create_follow_up_support_task_rejects_cross_module_parent(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        fake_enqueue_task_execution,
    )

    auth = _register_and_login(client, email="support-follow-up-3@example.com", name="Support Follow Up 3")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    support_workspace_id = _create_workspace(client, auth["token"], workspace_type="support", name="Support Demo")

    parent_task = task_repository.create_task(
        workspace_id=support_workspace_id,
        task_type="research_summary",
        created_by=auth["user_id"],
        input_json={"goal": "Summarize the workspace"},
    )

    running_parent = task_repository.update_task_status(parent_task.id, next_status="running")
    assert running_parent is not None
    completed_parent = task_repository.update_task_status(
        parent_task.id,
        next_status="done",
        output_json={"result": {"module_type": "research", "task_type": "research_summary"}},
    )
    assert completed_parent is not None

    follow_up_response = client.post(
        f"/api/v1/workspaces/{support_workspace_id}/tasks",
        json={
            "task_type": "ticket_summary",
            "input": {
                "parent_task_id": parent_task.id,
                "follow_up_notes": "Use this as a support follow-up.",
            },
        },
        headers=headers,
    )

    assert follow_up_response.status_code == 400
    assert "父任务必须是已完成的 Support 任务" in follow_up_response.json()["detail"]


def test_create_task_rejects_invalid_support_task_input(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        fake_enqueue_task_execution,
    )

    auth = _register_and_login(client, email="support-owner-invalid@example.com", name="Support Owner Invalid")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"], workspace_type="support")

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "ticket_summary",
            "input": {
                "customer_issue": "Customer billing question",
                "severity": "urgent",
            },
        },
        headers=headers,
    )

    assert response.status_code == 400
    assert "Support 任务输入无效" in response.json()["detail"]


def test_create_job_task_for_job_workspace_member(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        fake_enqueue_task_execution,
    )

    auth = _register_and_login(client, email="job-owner@example.com", name="Job Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"], workspace_type="job")

    create_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "resume_match",
            "input": {
                "target_role": " Platform engineer ",
                "seniority": " senior ",
                "must_have_skills": ["Python", "System design", "Python"],
                "preferred_skills": ["Reliability", "Mentorship"],
                "hiring_context": " Core platform modernization ",
            },
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    created_task = create_response.json()
    assert created_task["task_type"] == "resume_match"
    assert created_task["status"] == "pending"
    assert created_task["input_json"] == {
        "target_role": "Platform engineer",
        "seniority": "senior",
        "must_have_skills": ["Python", "System design"],
        "preferred_skills": ["Reliability", "Mentorship"],
        "hiring_context": "Core platform modernization",
    }


def test_create_job_shortlist_task_accepts_completed_comparison_tasks(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        fake_enqueue_task_execution,
    )

    auth = _register_and_login(client, email="job-shortlist-owner@example.com", name="Job Shortlist Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"], workspace_type="job")

    comparison_task_a = _create_completed_job_review_task(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        target_role="Platform engineer",
        candidate_label="Candidate A",
        summary="Grounded Python and platform ownership evidence exists.",
    )
    comparison_task_b = _create_completed_job_review_task(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        target_role="Platform engineer",
        candidate_label="Candidate B",
        summary="Grounded systems-design evidence exists, but reliability depth is thinner.",
        fit_signal="insufficient_grounding",
        evidence_status="documents_only",
        recommended_outcome="collect_more_hiring_signal",
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "resume_match",
            "input": {
                "target_role": " Platform engineer ",
                "comparison_task_ids": [comparison_task_a, comparison_task_b],
                "comparison_notes": " Prioritize backend ownership and platform depth. ",
            },
        },
        headers=headers,
    )

    assert response.status_code == 201
    created_task = response.json()
    assert created_task["input_json"] == {
        "target_role": "Platform engineer",
        "comparison_task_ids": [comparison_task_a, comparison_task_b],
        "comparison_notes": "Prioritize backend ownership and platform depth.",
    }


def test_create_job_shortlist_task_rejects_too_few_comparison_tasks(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        fake_enqueue_task_execution,
    )

    auth = _register_and_login(client, email="job-shortlist-owner-2@example.com", name="Job Shortlist Owner 2")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"], workspace_type="job")

    comparison_task_id = _create_completed_job_review_task(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        target_role="Platform engineer",
        candidate_label="Candidate Solo",
        summary="Only one candidate review exists.",
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "resume_match",
            "input": {
                "target_role": "Platform engineer",
                "comparison_task_ids": [comparison_task_id],
            },
        },
        headers=headers,
    )

    assert response.status_code == 400
    assert "至少需要两个对比招聘任务" in response.json()["detail"]


def test_create_job_shortlist_task_rejects_prior_shortlist_as_comparison_source(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        fake_enqueue_task_execution,
    )

    auth = _register_and_login(client, email="job-shortlist-owner-3@example.com", name="Job Shortlist Owner 3")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"], workspace_type="job")

    valid_task_id = _create_completed_job_review_task(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        target_role="Platform engineer",
        candidate_label="Candidate A",
        summary="Grounded backend evidence exists.",
    )
    nested_shortlist_id = _create_completed_job_review_task(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        target_role="Platform engineer",
        candidate_label="Candidate Nested",
        summary="This fixture will be mutated into a shortlist task.",
    )
    nested_shortlist = task_repository.get_task(nested_shortlist_id)
    assert nested_shortlist is not None
    nested_output = dict(nested_shortlist.output_json)
    nested_result = dict(nested_output["result"])
    nested_result["input"] = {
        "target_role": "Platform engineer",
        "comparison_task_ids": [valid_task_id, nested_shortlist_id],
    }
    updated_nested_task = task_repository.update_task_status(
        nested_shortlist_id,
        next_status="done",
        output_json={"result": nested_result},
    )
    assert updated_nested_task is not None

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "resume_match",
            "input": {
                "target_role": "Platform engineer",
                "comparison_task_ids": [valid_task_id, nested_shortlist_id],
            },
        },
        headers=headers,
    )

    assert response.status_code == 400
    assert "不能引用已有短名单" in response.json()["detail"]



def test_task_routes_scope_access_to_workspace_membership(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        fake_enqueue_task_execution,
    )

    owner_auth = _register_and_login(client, email="owner@example.com", name="Owner")
    other_auth = _register_and_login(client, email="other@example.com", name="Other")

    owner_headers = {"Authorization": f"Bearer {owner_auth['token']}"}
    other_headers = {"Authorization": f"Bearer {other_auth['token']}"}

    workspace_id = _create_workspace(client, owner_auth["token"])
    create_task_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={"task_type": "workspace_report", "input": {}},
        headers=owner_headers,
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    other_get_response = client.get(f"/api/v1/tasks/{task_id}", headers=other_headers)
    assert other_get_response.status_code == 404

    other_list_response = client.get(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        headers=other_headers,
    )
    assert other_list_response.status_code == 404



def test_create_task_rejects_unsupported_task_type(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        fake_enqueue_task_execution,
    )

    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={"task_type": "unsupported_task", "input": {}},
        headers=headers,
    )

    assert response.status_code == 422
    assert "task_type" in response.json()["detail"][0]["loc"]



def test_create_task_rejects_invalid_module_task_combination(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        fake_enqueue_task_execution,
    )

    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"], workspace_type="support")

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={"task_type": "research_summary", "input": {"goal": "Summarize support docs"}},
        headers=headers,
    )

    assert response.status_code == 400
    assert (
        "Task type research_summary is not supported for workspace module support"
        in response.json()["detail"]
    )



def test_create_task_rejects_invalid_support_module_task_combination(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        fake_enqueue_task_execution,
    )

    auth = _register_and_login(client, email="research-owner@example.com", name="Research Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"], workspace_type="research")

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={"task_type": "ticket_summary", "input": {"customer_issue": "Billing problem"}},
        headers=headers,
    )

    assert response.status_code == 400
    assert (
        "Task type ticket_summary is not supported for workspace module research"
        in response.json()["detail"]
    )


def test_create_task_rejects_invalid_job_module_task_combination(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        fake_enqueue_task_execution,
    )

    auth = _register_and_login(client, email="support-owner@example.com", name="Support Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"], workspace_type="support")

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={"task_type": "jd_summary", "input": {"target_role": "Platform engineer"}},
        headers=headers,
    )

    assert response.status_code == 400
    assert (
        "Task type jd_summary is not supported for workspace module support"
        in response.json()["detail"]
    )


def test_create_task_rejects_invalid_job_task_input(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        fake_enqueue_task_execution,
    )

    auth = _register_and_login(client, email="job-owner-2@example.com", name="Job Owner 2")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"], workspace_type="job")

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={"task_type": "jd_summary", "input": {"target_role": {"role": "Engineer"}}},
        headers=headers,
    )

    assert response.status_code == 400
    assert "Job 任务输入无效" in response.json()["detail"]



def test_create_task_rejects_invalid_research_task_input(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        fake_enqueue_task_execution,
    )

    auth = _register_and_login(client, email="research-owner-2@example.com", name="Research Owner 2")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "research_summary",
            "input": {"key_questions": [{"question": "bad"}]},
        },
        headers=headers,
    )

    assert response.status_code == 400
    assert "Research 任务输入无效" in response.json()["detail"]


def test_create_task_returns_500_and_marks_failed_when_queueing_fails(
    client: TestClient,
    monkeypatch,
) -> None:
    async def failing_enqueue_task_execution(task_id: str) -> str:
        raise TaskExecutionError("Redis unavailable")

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        failing_enqueue_task_execution,
    )

    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    create_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={"task_type": "research_summary", "input": {"goal": "Queue this task"}},
        headers=headers,
    )
    assert create_response.status_code == 500
    assert "Redis unavailable" in create_response.json()["detail"]

    list_response = client.get(f"/api/v1/workspaces/{workspace_id}/tasks", headers=headers)
    assert list_response.status_code == 200
    tasks = list_response.json()
    assert len(tasks) == 1
    assert tasks[0]["status"] == "failed"
    assert tasks[0]["error_message"] == "Redis unavailable"


def test_cancel_pending_task_marks_it_failed_with_control_state(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        fake_enqueue_task_execution,
    )

    auth = _register_and_login(client, email="cancel-owner@example.com", name="Cancel Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    create_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={"task_type": "research_summary", "input": {"goal": "Cancel this task"}},
        headers=headers,
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    cancel_response = client.post(
        f"/api/v1/tasks/{task_id}/cancel",
        json={"reason": "Duplicate request."},
        headers=headers,
    )
    assert cancel_response.status_code == 200
    cancelled_task = cancel_response.json()
    assert cancelled_task["status"] == "failed"
    assert cancelled_task["recovery_state"] == "cancelled"
    assert cancelled_task["recovery_detail"]["state"] == "cancelled"
    assert cancelled_task["recovery_detail"]["history"][-1]["event"] == "cancelled"
    assert cancelled_task["control_json"]["last_action"] == "cancel"
    assert cancelled_task["control_json"]["state"] == "cancelled"


def test_retry_failed_task_creates_linked_retry_attempt(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        fake_enqueue_task_execution,
    )

    auth = _register_and_login(client, email="retry-owner@example.com", name="Retry Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    create_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={"task_type": "research_summary", "input": {"goal": "Retry this task"}},
        headers=headers,
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    failed_task = task_repository.update_task_status(
        task_id,
        next_status="failed",
        error_message="Vector store unavailable",
    )
    assert failed_task is not None

    retry_response = client.post(
        f"/api/v1/tasks/{task_id}/retry",
        json={"reason": "Retry after transient failure."},
        headers=headers,
    )
    assert retry_response.status_code == 200
    retry_task = retry_response.json()
    assert retry_task["status"] == "pending"
    assert retry_task["recovery_state"] == "retry_attempt"
    assert retry_task["recovery_detail"]["source_task_id"] == task_id
    assert retry_task["recovery_detail"]["history"][-1]["event"] == "retry_attempt"
    assert retry_task["control_json"]["source_task_id"] == task_id

    original_task = task_repository.get_task(task_id)
    assert original_task is not None
    assert original_task.control_json["state"] == "retry_created"
    assert original_task.control_json["target_task_id"] == retry_task["id"]

    second_retry_response = client.post(
        f"/api/v1/tasks/{task_id}/retry",
        json={"reason": "Retry after transient failure."},
        headers=headers,
    )
    assert second_retry_response.status_code == 200
    assert second_retry_response.json()["id"] == retry_task["id"]
def test_create_support_task_rejects_goal_alias_input(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        fake_enqueue_task_execution,
    )

    auth = _register_and_login(client, email="support-owner-goal@example.com", name="Support Owner Goal")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"], workspace_type="support")

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "ticket_summary",
            "input": {"goal": "Customer cannot log in"},
        },
        headers=headers,
    )

    assert response.status_code == 400
    assert "customer_issue instead of goal" in response.json()["detail"]


def test_create_job_task_rejects_goal_alias_input(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr(
        "app.services.task_service.enqueue_task_execution",
        fake_enqueue_task_execution,
    )

    auth = _register_and_login(client, email="job-owner-goal@example.com", name="Job Owner Goal")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"], workspace_type="job")

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "jd_summary",
            "input": {"goal": "Platform engineer"},
        },
        headers=headers,
    )

    assert response.status_code == 400
    assert "target_role instead of goal" in response.json()["detail"]
