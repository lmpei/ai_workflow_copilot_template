from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import session_scope
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.trace import Trace


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


def test_chat_creates_conversation_messages_and_trace(client: TestClient) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    unauthorized_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/chat",
        json={"question": "What is this?", "mode": "rag"},
    )
    assert unauthorized_response.status_code == 401

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/chat",
        json={"question": "What is this?", "mode": "rag"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["sources"] == []
    assert "trace_id" in data

    with session_scope() as session:
        conversations = list(session.scalars(select(Conversation)))
        messages = list(session.scalars(select(Message).order_by(Message.created_at.asc())))
        traces = list(session.scalars(select(Trace)))

    assert len(conversations) == 1
    assert conversations[0].workspace_id == workspace_id
    assert conversations[0].user_id == auth["user_id"]
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[0].content == "What is this?"
    assert messages[1].role == "assistant"
    assert traces[0].id == data["trace_id"]
    assert traces[0].trace_type == "rag"


def test_chat_reuses_existing_conversation_id(client: TestClient) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    workspace_id = _create_workspace(client, auth["token"])

    first_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/chat",
        json={"question": "First question", "mode": "rag"},
        headers=headers,
    )
    assert first_response.status_code == 200

    with session_scope() as session:
        conversation = session.scalar(select(Conversation))

    second_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/chat",
        json={
            "question": "Second question",
            "mode": "rag",
            "conversation_id": conversation.id,
        },
        headers=headers,
    )
    assert second_response.status_code == 200

    with session_scope() as session:
        conversations = list(session.scalars(select(Conversation)))
        messages = list(session.scalars(select(Message).order_by(Message.created_at.asc())))
        traces = list(session.scalars(select(Trace).order_by(Trace.created_at.asc())))

    assert len(conversations) == 1
    assert [message.role for message in messages] == ["user", "assistant", "user", "assistant"]
    assert [trace.trace_type for trace in traces] == ["rag", "rag"]


def test_chat_rejects_foreign_conversation_id(client: TestClient) -> None:
    auth = _register_and_login(client, email="owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {auth['token']}"}
    first_workspace_id = _create_workspace(client, auth["token"], name="Workspace One")
    second_workspace_id = _create_workspace(client, auth["token"], name="Workspace Two")

    first_response = client.post(
        f"/api/v1/workspaces/{first_workspace_id}/chat",
        json={"question": "Owner question", "mode": "rag"},
        headers=headers,
    )
    assert first_response.status_code == 200

    with session_scope() as session:
        conversation = session.scalar(select(Conversation))

    response = client.post(
        f"/api/v1/workspaces/{second_workspace_id}/chat",
        json={
            "question": "Second workspace question",
            "mode": "rag",
            "conversation_id": conversation.id,
        },
        headers=headers,
    )
    assert response.status_code == 404
