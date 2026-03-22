from fastapi.testclient import TestClient


def test_list_scenario_modules_returns_canonical_registry(client: TestClient) -> None:
    response = client.get("/api/v1/scenario-modules")

    assert response.status_code == 200
    modules = response.json()
    assert [module["module_type"] for module in modules] == ["research", "support", "job"]
    assert modules[0]["entry_task_types"] == ["research_summary", "workspace_report"]
    assert modules[1]["task_labels"]["reply_draft"] == "Reply Draft"
    assert modules[2]["eval_prompt_field"] == "target_role"