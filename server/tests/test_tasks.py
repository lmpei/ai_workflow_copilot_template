from fastapi.testclient import TestClient

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


def _create_workspace(client: TestClient, token: str, *, name: str = "Research Demo") -> str:
    response = client.post(
        "/api/v1/workspaces",
        json={"name": name, "type": "research"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    return response.json()["id"]


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

    assert response.status_code == 400
    assert "Unsupported task type" in response.json()["detail"]


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
