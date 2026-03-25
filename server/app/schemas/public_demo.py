from pydantic import BaseModel


class PublicDemoSettingsResponse(BaseModel):
    public_demo_mode: bool
    registration_enabled: bool
    max_workspaces_per_user: int
    max_documents_per_workspace: int
    max_tasks_per_workspace: int
    max_upload_bytes: int
