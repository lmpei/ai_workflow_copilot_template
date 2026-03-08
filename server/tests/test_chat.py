from fastapi.testclient import TestClient


def test_chat_returns_stub_answer(client: TestClient) -> None:
    response = client.post(
        "/api/v1/workspaces/demo/chat",
        json={"question": "What is this?", "mode": "rag"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "trace_id" in data
