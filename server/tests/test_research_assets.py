from fastapi.testclient import TestClient

from app.repositories import research_asset_repository, task_repository


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


def _create_workspace(client: TestClient, token: str, *, name: str = "Research Demo") -> str:
    response = client.post(
        "/api/v1/workspaces",
        json={"name": name, "module_type": "research"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _complete_research_task(task_id: str, *, summary: str, goal: str) -> None:
    running_task = task_repository.update_task_status(task_id, next_status="running")
    assert running_task is not None
    completed_task = task_repository.update_task_status(
        task_id,
        next_status="done",
        output_json={
            "task_id": task_id,
            "task_type": "workspace_report",
            "worker": "arq",
            "status": "completed",
            "result": {
                "module_type": "research",
                "task_type": "workspace_report",
                "title": "Workspace Report",
                "summary": summary,
                "input": {
                    "goal": goal,
                    "deliverable": "report",
                    "requested_sections": ["summary", "findings", "evidence", "open_questions", "next_steps"],
                },
                "sections": {
                    "summary": summary,
                    "findings": [],
                    "evidence_overview": [],
                    "open_questions": [],
                    "next_steps": [],
                },
                "report": {
                    "headline": f"Research Report: {goal}",
                    "executive_summary": summary,
                    "sections": [],
                    "open_questions": [],
                    "recommended_next_steps": [],
                    "evidence_ref_ids": [],
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
    assert completed_task is not None


def test_create_list_and_get_research_assets(client: TestClient, monkeypatch) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr("app.services.task_service.enqueue_task_execution", fake_enqueue_task_execution)

    auth = _register_and_login(client, email="asset-owner@example.com", name="Asset Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    task_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "workspace_report",
            "input": {"goal": "Create a baseline report", "deliverable": "report"},
        },
        headers=headers,
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]
    _complete_research_task(
        task_id,
        summary="Delayed sign-off is the strongest current risk.",
        goal="Create a baseline report",
    )

    create_asset_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/research-assets",
        json={"task_id": task_id, "title": "Apollo risk workbench"},
        headers=headers,
    )
    assert create_asset_response.status_code == 201
    created_asset = create_asset_response.json()
    assert created_asset["title"] == "Apollo risk workbench"
    assert created_asset["latest_task_id"] == task_id
    assert created_asset["latest_revision_number"] == 1
    assert created_asset["revisions"][0]["revision_number"] == 1
    assert created_asset["revisions"][0]["task_id"] == task_id

    list_response = client.get(
        f"/api/v1/workspaces/{workspace_id}/research-assets",
        headers=headers,
    )
    assert list_response.status_code == 200
    listed_assets = list_response.json()
    assert len(listed_assets) == 1
    assert listed_assets[0]["id"] == created_asset["id"]
    assert listed_assets[0]["latest_summary"] == "Delayed sign-off is the strongest current risk."

    get_response = client.get(
        f"/api/v1/research-assets/{created_asset['id']}",
        headers=headers,
    )
    assert get_response.status_code == 200
    loaded_asset = get_response.json()
    assert loaded_asset["id"] == created_asset["id"]
    assert loaded_asset["latest_result_json"]["summary"] == "Delayed sign-off is the strongest current risk."

    persisted_task = task_repository.get_task(task_id)
    assert persisted_task is not None
    assert persisted_task.output_json["result"]["metadata"]["research_asset"]["asset_id"] == created_asset["id"]


def test_create_research_asset_is_idempotent_for_same_task(client: TestClient, monkeypatch) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr("app.services.task_service.enqueue_task_execution", fake_enqueue_task_execution)

    auth = _register_and_login(client, email="asset-owner-2@example.com", name="Asset Owner 2")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    task_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "workspace_report",
            "input": {"goal": "Create a baseline report", "deliverable": "report"},
        },
        headers=headers,
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]
    _complete_research_task(
        task_id,
        summary="Delayed sign-off is the strongest current risk.",
        goal="Create a baseline report",
    )

    first_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/research-assets",
        json={"task_id": task_id},
        headers=headers,
    )
    second_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/research-assets",
        json={"task_id": task_id},
        headers=headers,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert first_response.json()["id"] == second_response.json()["id"]
    assert len(research_asset_repository.list_workspace_research_assets(workspace_id, auth["user_id"])) == 1


def test_create_task_accepts_linked_research_asset(client: TestClient, monkeypatch) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr("app.services.task_service.enqueue_task_execution", fake_enqueue_task_execution)

    auth = _register_and_login(client, email="asset-owner-3@example.com", name="Asset Owner 3")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    task_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "workspace_report",
            "input": {"goal": "Create a baseline report", "deliverable": "report"},
        },
        headers=headers,
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]
    _complete_research_task(
        task_id,
        summary="Delayed sign-off is the strongest current risk.",
        goal="Create a baseline report",
    )

    asset_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/research-assets",
        json={"task_id": task_id},
        headers=headers,
    )
    assert asset_response.status_code == 201
    asset_id = asset_response.json()["id"]

    follow_up_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "workspace_report",
            "input": {
                "goal": "Revise the baseline report",
                "deliverable": "report",
                "research_asset_id": asset_id,
                "parent_task_id": task_id,
                "continuation_notes": "Focus on unresolved ownership evidence.",
            },
        },
        headers=headers,
    )
    assert follow_up_response.status_code == 201
    created_task = follow_up_response.json()
    assert created_task["input_json"]["research_asset_id"] == asset_id
    assert created_task["input_json"]["parent_task_id"] == task_id


def test_create_task_rejects_invalid_research_asset_reference(client: TestClient, monkeypatch) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr("app.services.task_service.enqueue_task_execution", fake_enqueue_task_execution)

    auth = _register_and_login(client, email="asset-owner-4@example.com", name="Asset Owner 4")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "workspace_report",
            "input": {
                "goal": "Revise the baseline report",
                "deliverable": "report",
                "research_asset_id": "missing-asset",
            },
        },
        headers=headers,
    )

    assert response.status_code == 400
    assert "Research asset not found in this workspace" in response.json()["detail"]


def test_create_task_rejects_parent_task_linked_to_different_research_asset(
    client: TestClient,
    monkeypatch,
) -> None:
    async def fake_enqueue_task_execution(task_id: str) -> str:
        return f"job-{task_id}"

    monkeypatch.setattr("app.services.task_service.enqueue_task_execution", fake_enqueue_task_execution)

    auth = _register_and_login(client, email="asset-owner-5@example.com", name="Asset Owner 5")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    first_task_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "workspace_report",
            "input": {"goal": "Create report one", "deliverable": "report"},
        },
        headers=headers,
    )
    second_task_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "workspace_report",
            "input": {"goal": "Create report two", "deliverable": "report"},
        },
        headers=headers,
    )
    assert first_task_response.status_code == 201
    assert second_task_response.status_code == 201

    first_task_id = first_task_response.json()["id"]
    second_task_id = second_task_response.json()["id"]
    _complete_research_task(first_task_id, summary="First report summary.", goal="Create report one")
    _complete_research_task(second_task_id, summary="Second report summary.", goal="Create report two")

    first_asset_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/research-assets",
        json={"task_id": first_task_id},
        headers=headers,
    )
    second_asset_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/research-assets",
        json={"task_id": second_task_id},
        headers=headers,
    )
    assert first_asset_response.status_code == 201
    assert second_asset_response.status_code == 201

    mismatched_follow_up_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/tasks",
        json={
            "task_type": "workspace_report",
            "input": {
                "goal": "Revise the first report",
                "deliverable": "report",
                "research_asset_id": second_asset_response.json()["id"],
                "parent_task_id": first_task_id,
            },
        },
        headers=headers,
    )

    assert mismatched_follow_up_response.status_code == 400
    assert "Parent research task is linked to a different Research asset" in mismatched_follow_up_response.json()["detail"]
