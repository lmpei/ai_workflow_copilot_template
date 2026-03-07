from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    workspace_id: str
    title: str
    source_type: str
    file_path: str | None = None
    mime_type: str | None = None
    status: str
    created_by: str
    created_at: datetime
    updated_at: datetime
