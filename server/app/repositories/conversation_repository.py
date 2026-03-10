from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select

from app.core.database import session_scope
from app.models.conversation import Conversation
from app.models.message import Message


def get_conversation(conversation_id: str, workspace_id: str, user_id: str) -> Conversation | None:
    with session_scope() as session:
        statement = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.workspace_id == workspace_id,
            Conversation.user_id == user_id,
        )
        return session.scalar(statement)


def create_conversation(*, workspace_id: str, user_id: str, title: str) -> Conversation:
    now = datetime.now(UTC)
    conversation = Conversation(
        id=str(uuid4()),
        workspace_id=workspace_id,
        user_id=user_id,
        title=title,
        created_at=now,
        updated_at=now,
    )
    with session_scope() as session:
        session.add(conversation)
        session.flush()
        session.refresh(conversation)
        return conversation


def create_message(
    *,
    conversation_id: str,
    role: str,
    content: str,
    metadata_json: dict | None = None,
) -> Message:
    message = Message(
        id=str(uuid4()),
        conversation_id=conversation_id,
        role=role,
        content=content,
        metadata_json=metadata_json or {},
    )
    with session_scope() as session:
        session.add(message)
        session.flush()
        session.refresh(message)
        return message


def touch_conversation(conversation_id: str) -> None:
    with session_scope() as session:
        conversation = session.get(Conversation, conversation_id)
        if conversation is None:
            return

        conversation.updated_at = datetime.now(UTC)
        session.add(conversation)
