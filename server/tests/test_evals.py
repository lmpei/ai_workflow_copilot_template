from fastapi.testclient import TestClient


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
