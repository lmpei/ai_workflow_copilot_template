from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class Document:
    id: str
    workspace_id: str
    title: str
    source_type: str = "upload"
    file_path: str | None = None
    mime_type: str | None = None
    status: str = "uploaded"
    created_by: str = "demo-user"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
