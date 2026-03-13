import shutil
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.repositories.document_repository import create_document, list_document_chunks
from app.services import document_service
from app.services.document_service import (
    DocumentProcessingError,
    ParsedDocumentSegment,
    get_document,
    parse_document_into_chunks,
)

UPLOAD_ROOT = Path("storage") / "uploads"


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


def _create_uploaded_document(
    *,
    workspace_id: str,
    user_id: str,
    filename: str,
    content: bytes,
    mime_type: str,
) -> dict[str, str]:
    document_id = str(uuid4())
    relative_path = Path("uploads") / workspace_id / document_id / filename
    full_path = Path("storage") / relative_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_bytes(content)

    document = create_document(
        document_id=document_id,
        workspace_id=workspace_id,
        title=filename,
        file_path=relative_path.as_posix(),
        mime_type=mime_type,
        created_by=user_id,
    )
    return {
        "id": document.id,
        "file_path": document.file_path or "",
    }


def setup_function() -> None:
    shutil.rmtree(UPLOAD_ROOT, ignore_errors=True)


def teardown_function() -> None:
    shutil.rmtree(UPLOAD_ROOT, ignore_errors=True)


def test_parse_plain_text_document_into_ordered_chunks(client: TestClient) -> None:
    auth = _register_and_login(client, email="plain-owner@example.com", name="Owner")
    workspace_id = _create_workspace(client, auth["token"])
    long_text = ("Alpha beta gamma delta " * 120).encode("utf-8")
    uploaded = _create_uploaded_document(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        filename="knowledge.txt",
        content=long_text,
        mime_type="text/plain",
    )

    parsed_document = parse_document_into_chunks(
        document_id=uploaded["id"],
        user_id=auth["user_id"],
    )

    chunks = list_document_chunks(uploaded["id"])
    assert parsed_document.status == "chunked"
    assert len(chunks) >= 2
    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))
    assert chunks[0].metadata_json["char_start"] == 0
    assert chunks[0].metadata_json["char_end"] > chunks[0].metadata_json["char_start"]
    assert all(chunk.content for chunk in chunks)


def test_parse_small_markdown_document_produces_single_chunk(client: TestClient) -> None:
    auth = _register_and_login(client, email="markdown-owner@example.com", name="Owner")
    workspace_id = _create_workspace(client, auth["token"])
    uploaded = _create_uploaded_document(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        filename="notes.md",
        content=b"# Summary\n\n- first point\n- second point\n",
        mime_type="text/markdown",
    )

    parsed_document = parse_document_into_chunks(
        document_id=uploaded["id"],
        user_id=auth["user_id"],
    )

    chunks = list_document_chunks(uploaded["id"])
    assert parsed_document.status == "chunked"
    assert len(chunks) == 1
    assert "# Summary" in chunks[0].content
    assert chunks[0].metadata_json["char_start"] == 0


def test_parse_pdf_document_uses_pdf_parser_and_preserves_page_metadata(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    auth = _register_and_login(client, email="pdf-owner@example.com", name="Owner")
    workspace_id = _create_workspace(client, auth["token"])
    uploaded = _create_uploaded_document(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        filename="report.pdf",
        content=b"%PDF-1.4 fake content",
        mime_type="application/pdf",
    )

    monkeypatch.setattr(
        document_service,
        "_parse_pdf_segments",
        lambda _path: [
            ParsedDocumentSegment(
                text="PDF page content for parsing",
                metadata={"page_number": 1},
            ),
        ],
    )

    parsed_document = parse_document_into_chunks(
        document_id=uploaded["id"],
        user_id=auth["user_id"],
    )

    chunks = list_document_chunks(uploaded["id"])
    assert parsed_document.status == "chunked"
    assert len(chunks) == 1
    assert chunks[0].metadata_json["page_number"] == 1


def test_parse_unsupported_document_marks_document_failed(client: TestClient) -> None:
    auth = _register_and_login(client, email="unsupported-owner@example.com", name="Owner")
    workspace_id = _create_workspace(client, auth["token"])
    uploaded = _create_uploaded_document(
        workspace_id=workspace_id,
        user_id=auth["user_id"],
        filename="payload.json",
        content=b'{\"hello\": \"world\"}',
        mime_type="application/json",
    )

    with pytest.raises(DocumentProcessingError, match="Unsupported document type"):
        parse_document_into_chunks(
            document_id=uploaded["id"],
            user_id=auth["user_id"],
        )

    document = get_document(document_id=uploaded["id"], user_id=auth["user_id"])
    assert document is not None
    assert document.status == "failed"
    assert list_document_chunks(uploaded["id"]) == []
