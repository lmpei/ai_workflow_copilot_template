from pathlib import Path

from app.core.config import get_settings
from app.repositories import workspace_repository
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate
from app.services.document_parsing_service import DocumentProcessingError, resolve_document_path
from app.services.indexing_service import DocumentIndexingError, get_vector_store
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


def _cleanup_workspace_files(file_paths: list[str]) -> None:
    uploads_root = (Path("storage") / "uploads").resolve()
    for file_path in file_paths:
        try:
            resolved_path = resolve_document_path(file_path).resolve()
        except (DocumentProcessingError, OSError):
            continue

        if uploads_root not in resolved_path.parents:
            continue

        try:
            resolved_path.unlink(missing_ok=True)
        except OSError:
            continue

        current_dir = resolved_path.parent
        while current_dir != uploads_root and uploads_root in current_dir.parents:
            try:
                current_dir.rmdir()
            except OSError:
                break
            current_dir = current_dir.parent


def _cleanup_workspace_vectors(vector_ids: list[str]) -> None:
    if not vector_ids:
        return

    try:
        vector_store = get_vector_store()
        vector_store.delete_embeddings(
            collection_name=get_settings().chroma_collection_name,
            ids=vector_ids,
        )
    except DocumentIndexingError:
        return


def delete_workspace(workspace_id: str, user_id: str) -> bool:
    deleted = workspace_repository.delete_workspace_tree(
        workspace_id=workspace_id,
        user_id=user_id,
    )
    if deleted is None:
        return False

    _cleanup_workspace_files(deleted.file_paths)
    _cleanup_workspace_vectors(deleted.vector_ids)
    return True
