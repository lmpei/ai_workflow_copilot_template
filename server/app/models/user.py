from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class User:
    id: str
    email: str
    password_hash: str
    name: str
    role: str = "member"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
