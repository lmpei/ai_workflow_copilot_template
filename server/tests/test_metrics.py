from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy import select

from app.core.database import session_scope
from app.models.trace import Trace
from app.repositories import eval_repository, task_repository
from app.services import retrieval_service


class _FallbackRetriever:
    def retrieve(self, *, workspace_id: str, question: str) -> list[object]:
        return []


class _UnusedAnswerGenerator:
    def generate_answer(self, *, question: str, retrieved_chunks: list[object]) -> object:
        raise AssertionError(
            "Answer generator should not be called when retrieval returns no chunks",
        )


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


def test_metrics_returns_zeroed_values_for_empty_workspace(client: TestClient) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    response = client.get(f"/api/v1/workspaces/{workspace_id}/metrics", headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        "workspace_id": workspace_id,
        "total_requests": 0,
        "avg_latency_ms": 0,
        "retrieval_hit_count": 0,
        "retrieval_hit_rate": 0.0,
        "token_usage": 0,
        "total_estimated_cost": 0.0,
        "task_success_rate": 0.0,
        "eval_run_count": 0,
        "eval_case_count": 0,
        "eval_pass_rate": 0.0,
        "avg_eval_score": 0.0,
    }


def test_metrics_aggregate_persisted_traces(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])
    monkeypatch.setattr(retrieval_service, "get_retriever", lambda: _FallbackRetriever())
    monkeypatch.setattr(
        retrieval_service,
        "get_answer_generator",
        lambda: _UnusedAnswerGenerator(),
    )

    first_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/chat",
        json={"question": "First question", "mode": "rag"},
        headers=headers,
    )
    second_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/chat",
        json={"question": "Second question", "mode": "rag"},
        headers=headers,
    )
    assert first_response.status_code == 200
    assert second_response.status_code == 200

    with session_scope() as session:
        traces = list(session.scalars(select(Trace).where(Trace.workspace_id == workspace_id)))

    expected_total_requests = len(traces)
    expected_avg_latency_ms = int(
        sum(trace.latency_ms for trace in traces) / expected_total_requests
    )
    expected_token_usage = sum(trace.token_input + trace.token_output for trace in traces)
    expected_total_estimated_cost = round(sum(trace.estimated_cost for trace in traces), 6)

    task_done = task_repository.create_task(
        workspace_id=workspace_id,
        task_type="research_summary",
        created_by=auth["user_id"],
        status="running",
    )
    task_repository.update_task_status(
        task_done.id,
        next_status="done",
        output_json={"status": "ok"},
    )
    task_failed = task_repository.create_task(
        workspace_id=workspace_id,
        task_type="workspace_report",
        created_by=auth["user_id"],
    )
    task_repository.update_task_status(
        task_failed.id,
        next_status="failed",
        error_message="worker failed",
    )

    dataset = eval_repository.create_eval_dataset(
        workspace_id=workspace_id,
        name="Analytics Eval",
        eval_type="retrieval_chat",
        created_by=auth["user_id"],
    )
    eval_case = eval_repository.create_eval_case(
        dataset_id=dataset.id,
        case_index=0,
        input_json={"question": "Who owns Apollo?"},
    )
    eval_run = eval_repository.create_eval_run(
        workspace_id=workspace_id,
        dataset_id=dataset.id,
        eval_type=dataset.eval_type,
        created_by=auth["user_id"],
        summary_json={
            "total_cases": 1,
            "completed_cases": 1,
            "failed_cases": 0,
            "passed_cases": 1,
            "avg_score": 0.9,
            "pass_rate": 1.0,
        },
        status="completed",
    )
    eval_repository.create_eval_result(
        eval_run_id=eval_run.id,
        eval_case_id=eval_case.id,
        status="completed",
        output_json={"answer": "Alice"},
        metrics_json={"rule_score": 1.0, "judge_score": 0.8},
        score=0.9,
        passed=True,
    )

    response = client.get(f"/api/v1/workspaces/{workspace_id}/metrics", headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        "workspace_id": workspace_id,
        "total_requests": expected_total_requests,
        "avg_latency_ms": expected_avg_latency_ms,
        "retrieval_hit_count": 0,
        "retrieval_hit_rate": 0.0,
        "token_usage": expected_token_usage,
        "total_estimated_cost": expected_total_estimated_cost,
        "task_success_rate": 0.5,
        "eval_run_count": 1,
        "eval_case_count": 1,
        "eval_pass_rate": 1.0,
        "avg_eval_score": 0.9,
    }

    analytics_response = client.get(f"/api/v1/workspaces/{workspace_id}/analytics", headers=headers)
    assert analytics_response.status_code == 200
    assert analytics_response.json() == response.json()

    traces_response = client.get(f"/api/v1/workspaces/{workspace_id}/traces", headers=headers)
    assert traces_response.status_code == 200
    traces_payload = traces_response.json()
    assert len(traces_payload) == expected_total_requests
    assert all(trace["workspace_id"] == workspace_id for trace in traces_payload)


def test_metrics_reject_unauthorized_workspace_access(client: TestClient) -> None:
    owner_auth = _register_and_login(client, email="owner@example.com", name="Owner")
    other_auth = _register_and_login(client, email="other@example.com", name="Other")

    other_headers = {"Authorization": f"Bearer {other_auth['token']}"}
    workspace_id = _create_workspace(client, owner_auth["token"])

    unauthorized_response = client.get(f"/api/v1/workspaces/{workspace_id}/metrics")
    assert unauthorized_response.status_code == 401

    forbidden_response = client.get(
        f"/api/v1/workspaces/{workspace_id}/metrics",
        headers=other_headers,
    )
    assert forbidden_response.status_code == 404

    analytics_forbidden_response = client.get(
        f"/api/v1/workspaces/{workspace_id}/analytics",
        headers=other_headers,
    )
    assert analytics_forbidden_response.status_code == 404

    traces_forbidden_response = client.get(
        f"/api/v1/workspaces/{workspace_id}/traces",
        headers=other_headers,
    )
    assert traces_forbidden_response.status_code == 404

