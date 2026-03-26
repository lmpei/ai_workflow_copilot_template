from pydantic import BaseModel, Field

from app.schemas.document import DocumentResponse
from app.schemas.scenario import ModuleType, ScenarioTaskType
from app.schemas.workspace import WorkspaceResponse


class PublicDemoSettingsResponse(BaseModel):
    public_demo_mode: bool
    registration_enabled: bool
    max_workspaces_per_user: int
    max_documents_per_workspace: int
    max_tasks_per_workspace: int
    max_upload_bytes: int


class PublicDemoSeedDocumentResponse(BaseModel):
    title: str
    summary: str


class PublicDemoShowcaseStepResponse(BaseModel):
    title: str
    description: str
    route_suffix: str
    cta_label: str
    sample_prompt: str | None = None
    sample_task_type: ScenarioTaskType | None = None
    sample_task_input: dict[str, object] = Field(default_factory=dict)


class PublicDemoTemplateResponse(BaseModel):
    template_id: str
    module_type: ModuleType
    title: str
    summary: str
    workspace_name: str
    workspace_description: str
    seeded_documents: list[PublicDemoSeedDocumentResponse] = Field(default_factory=list)
    showcase_steps: list[PublicDemoShowcaseStepResponse] = Field(default_factory=list)


class PublicDemoWorkspaceSeedResponse(BaseModel):
    workspace: WorkspaceResponse
    documents: list[DocumentResponse] = Field(default_factory=list)
    template: PublicDemoTemplateResponse
