from app.repositories import workspace_repository
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate
from app.services.public_demo_service import ensure_workspace_creation_allowed
from app.services.scenario_contract_service import resolve_workspace_module_contract


def list_workspaces(user_id: str) -> list[WorkspaceResponse]:
    workspaces = workspace_repository.list_workspaces(user_id=user_id)
    return [WorkspaceResponse.from_model(workspace) for workspace in workspaces]


def get_workspace(workspace_id: str, user_id: str) -> WorkspaceResponse | None:
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        return None
    return WorkspaceResponse.from_model(workspace)


def create_workspace(payload: WorkspaceCreate, owner_id: str) -> WorkspaceResponse:
    ensure_workspace_creation_allowed(user_id=owner_id)
    module_type, module_config_json = resolve_workspace_module_contract(
        requested_module_type=payload.module_type,
        requested_module_config_json=payload.module_config_json,
    )
    normalized_payload = payload.model_copy(
        update={
            "type": module_type,
            "module_type": module_type,
            "module_config_json": module_config_json,
        }
    )
    workspace = workspace_repository.create_workspace(payload=normalized_payload, owner_id=owner_id)
    return WorkspaceResponse.from_model(workspace)


def update_workspace(
    workspace_id: str,
    user_id: str,
    payload: WorkspaceUpdate,
) -> WorkspaceResponse | None:
    current_workspace = workspace_repository.get_workspace(
        workspace_id=workspace_id,
        user_id=user_id,
    )
    if current_workspace is None:
        return None

    has_module_contract_update = any(
        value is not None
        for value in (
            payload.module_type,
            payload.module_config_json,
        )
    )
    if has_module_contract_update:
        module_type, module_config_json = resolve_workspace_module_contract(
            current_module_type=current_workspace.module_type,
            current_module_config_json=current_workspace.module_config_json,
            requested_module_type=payload.module_type,
            requested_module_config_json=payload.module_config_json,
        )
        payload = payload.model_copy(
            update={
                "type": module_type,
                "module_type": module_type,
                "module_config_json": module_config_json,
            }
        )

    workspace = workspace_repository.update_workspace(
        workspace_id=workspace_id,
        user_id=user_id,
        payload=payload,
    )
    if workspace is None:
        return None
    return WorkspaceResponse.from_model(workspace)
