from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class Workspace:
    id: str
    owner_id: str
    name: str
    type: str = "research"
    description: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
