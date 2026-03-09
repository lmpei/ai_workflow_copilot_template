from datetime import UTC, datetime

from sqlalchemy import select

from app.core.database import session_scope
from app.models.document import Document
from app.models.workspace_member import WorkspaceMember


def user_has_workspace_access(workspace_id: str, user_id: str) -> bool:
    with session_scope() as session:
        statement = select(WorkspaceMember.id).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        return session.scalar(statement) is not None


def create_document(
    *,
    document_id: str,
    workspace_id: str,
    title: str,
    file_path: str,
    mime_type: str | None,
    created_by: str,
    source_type: str = "upload",
    status: str = "uploaded",
) -> Document:
    now = datetime.now(UTC)
    document = Document(
        id=document_id,
        workspace_id=workspace_id,
        title=title,
        source_type=source_type,
        file_path=file_path,
        mime_type=mime_type,
        status=status,
        created_by=created_by,
        created_at=now,
        updated_at=now,
    )
    with session_scope() as session:
        session.add(document)
        session.flush()
        session.refresh(document)
        return document


def list_documents(workspace_id: str, user_id: str) -> list[Document]:
    with session_scope() as session:
        statement = (
            select(Document)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Document.workspace_id)
            .where(
                Document.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
            .order_by(Document.created_at.asc())
        )
        result = session.scalars(statement)
        return list(result)


def get_document(document_id: str, user_id: str) -> Document | None:
    with session_scope() as session:
        statement = (
            select(Document)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Document.workspace_id)
            .where(
                Document.id == document_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        return session.scalar(statement)


def reindex_document(document_id: str, user_id: str) -> Document | None:
    with session_scope() as session:
        statement = (
            select(Document)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Document.workspace_id)
            .where(
                Document.id == document_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        document = session.scalar(statement)
        if document is None:
            return None

        document.status = "uploaded"
        document.updated_at = datetime.now(UTC)
        session.add(document)
        session.flush()
        session.refresh(document)
        return document
