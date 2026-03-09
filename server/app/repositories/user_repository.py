from uuid import uuid4

from sqlalchemy import select

from app.core.database import session_scope
from app.models.user import User


def get_user_by_email(email: str) -> User | None:
    with session_scope() as session:
        statement = select(User).where(User.email == email)
        return session.scalar(statement)


def get_user_by_id(user_id: str) -> User | None:
    with session_scope() as session:
        return session.get(User, user_id)


def create_user(
    *,
    email: str,
    password_hash: str,
    name: str,
    role: str = "owner",
) -> User:
    user = User(
        id=str(uuid4()),
        email=email,
        password_hash=password_hash,
        name=name,
        role=role,
    )

    with session_scope() as session:
        session.add(user)
        session.flush()
        session.refresh(user)
        return user
