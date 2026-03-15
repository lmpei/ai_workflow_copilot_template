import pytest
from fastapi.testclient import TestClient

from app.repositories import eval_repository
from app.services import eval_service
from app.services.eval_execution_service import EvalExecutionError


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



def _create_workspace(client: TestClient, token: str, *, name: str = "Eval Demo") -> str:
    response = client.post(
        "/api/v1/workspaces",
        json={"name": name, "type": "research"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.fixture(autouse=True)
def stub_eval_enqueue(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_enqueue_eval_run(eval_run_id: str) -> str:
        return f"job-{eval_run_id}"

    monkeypatch.setattr(eval_service, "enqueue_eval_run", fake_enqueue_eval_run)



def test_eval_api_creates_lists_datasets_and_creates_runs(client: TestClient) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    create_dataset_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/evals/datasets",
        json={
            "name": "Grounded Chat Dataset",
            "eval_type": "retrieval_chat",
            "cases": [
                {
                    "input_json": {"question": "Who owns Apollo?"},
                    "expected_json": {"answer_contains": ["Alice"]},
                },
                {
                    "input_json": {"question": "How many milestones are there?"},
                    "expected_json": {"answer_contains": ["three"]},
                    "metadata_json": {"document_id": "doc-1"},
                },
            ],
        },
        headers=headers,
    )
    assert create_dataset_response.status_code == 201
    dataset = create_dataset_response.json()
    assert dataset["name"] == "Grounded Chat Dataset"
    assert [item["case_index"] for item in dataset["cases"]] == [0, 1]

    list_datasets_response = client.get(
        f"/api/v1/workspaces/{workspace_id}/evals/datasets",
        headers=headers,
    )
    assert list_datasets_response.status_code == 200
    datasets = list_datasets_response.json()
    assert len(datasets) == 1
    assert datasets[0]["id"] == dataset["id"]
    assert len(datasets[0]["cases"]) == 2

    create_run_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/evals/runs",
        json={"dataset_id": dataset["id"]},
        headers=headers,
    )
    assert create_run_response.status_code == 201
    eval_run = create_run_response.json()
    assert eval_run["dataset_id"] == dataset["id"]
    assert eval_run["status"] == "pending"
    assert eval_run["summary_json"] == {
        "total_cases": 2,
        "completed_cases": 0,
        "failed_cases": 0,
    }

    get_run_response = client.get(
        f"/api/v1/evals/runs/{eval_run['id']}",
        headers=headers,
    )
    assert get_run_response.status_code == 200
    assert get_run_response.json()["id"] == eval_run["id"]

    eval_repository.create_eval_result(
        eval_run_id=eval_run["id"],
        eval_case_id=dataset["cases"][0]["id"],
        status="completed",
        output_json={"answer": "Alice"},
        metrics_json={"rule_score": 1.0, "judge_score": 0.8},
        score=0.9,
        passed=True,
    )
    results_response = client.get(
        f"/api/v1/evals/runs/{eval_run['id']}/results",
        headers=headers,
    )
    assert results_response.status_code == 200
    results = results_response.json()
    assert len(results) == 1
    assert results[0]["eval_run_id"] == eval_run["id"]
    assert results[0]["score"] == 0.9
    assert results[0]["passed"] is True



def test_eval_api_rejects_unauthorized_and_cross_workspace_access(client: TestClient) -> None:
    owner_auth = _register_and_login(client, email="owner@example.com", name="Owner")
    other_auth = _register_and_login(client, email="other@example.com", name="Other")
    owner_headers = {"Authorization": f"Bearer {owner_auth['token']}"}
    other_headers = {"Authorization": f"Bearer {other_auth['token']}"}
    owner_workspace_id = _create_workspace(client, owner_auth["token"], name="Owner Eval")

    unauthorized_response = client.get(f"/api/v1/workspaces/{owner_workspace_id}/evals/datasets")
    assert unauthorized_response.status_code == 401

    forbidden_list_response = client.get(
        f"/api/v1/workspaces/{owner_workspace_id}/evals/datasets",
        headers=other_headers,
    )
    assert forbidden_list_response.status_code == 404

    dataset_response = client.post(
        f"/api/v1/workspaces/{owner_workspace_id}/evals/datasets",
        json={
            "name": "Owner Dataset",
            "eval_type": "retrieval_chat",
            "cases": [{"input_json": {"question": "Who owns Apollo?"}}],
        },
        headers=owner_headers,
    )
    assert dataset_response.status_code == 201
    dataset_id = dataset_response.json()["id"]

    second_workspace_id = _create_workspace(client, owner_auth["token"], name="Second Eval")
    wrong_workspace_run_response = client.post(
        f"/api/v1/workspaces/{second_workspace_id}/evals/runs",
        json={"dataset_id": dataset_id},
        headers=owner_headers,
    )
    assert wrong_workspace_run_response.status_code == 404

    owner_run_response = client.post(
        f"/api/v1/workspaces/{owner_workspace_id}/evals/runs",
        json={"dataset_id": dataset_id},
        headers=owner_headers,
    )
    assert owner_run_response.status_code == 201
    owner_run_id = owner_run_response.json()["id"]

    foreign_results_response = client.get(
        f"/api/v1/evals/runs/{owner_run_id}/results",
        headers=other_headers,
    )
    assert foreign_results_response.status_code == 404



def test_eval_api_rejects_invalid_eval_type(client: TestClient) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/evals/datasets",
        json={
            "name": "Invalid Dataset",
            "eval_type": "agent_quality",
            "cases": [],
        },
        headers=headers,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported eval type: agent_quality"



def test_eval_api_marks_run_failed_when_enqueue_fails(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    auth = _register_and_login(client, email="queue-owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    dataset_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/evals/datasets",
        json={
            "name": "Queue Failure Dataset",
            "eval_type": "retrieval_chat",
            "cases": [{"input_json": {"question": "Who owns Apollo?"}}],
        },
        headers=headers,
    )
    assert dataset_response.status_code == 201
    dataset_id = dataset_response.json()["id"]

    async def failing_enqueue(_eval_run_id: str) -> str:
        raise EvalExecutionError("Redis unavailable")

    monkeypatch.setattr(eval_service, "enqueue_eval_run", failing_enqueue)

    create_run_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/evals/runs",
        json={"dataset_id": dataset_id},
        headers=headers,
    )

    assert create_run_response.status_code == 500
    assert create_run_response.json()["detail"] == "Redis unavailable"

    persisted_runs = eval_repository.list_workspace_eval_runs(workspace_id, auth["user_id"])
    assert len(persisted_runs) == 1
    assert persisted_runs[0].status == "failed"
    assert persisted_runs[0].error_message == "Redis unavailable"
