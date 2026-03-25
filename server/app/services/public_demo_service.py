from app.core.config import get_settings
from app.repositories import document_repository, task_repository, workspace_repository
from app.schemas.public_demo import PublicDemoSettingsResponse


class PublicDemoAccessError(Exception):
    pass


class PublicDemoLimitError(Exception):
    pass


class PublicDemoUploadLimitError(Exception):
    pass


def _format_upload_limit(max_upload_bytes: int) -> str:
    megabytes = max_upload_bytes / (1024 * 1024)
    if megabytes >= 1:
        if float(megabytes).is_integer():
            return f"{megabytes:.0f} MB"
        return f"{megabytes:.1f} MB"
    if max_upload_bytes == 1:
        return "1 byte"
    return f"{max_upload_bytes} bytes"


def get_public_demo_settings() -> PublicDemoSettingsResponse:
    settings = get_settings()
    return PublicDemoSettingsResponse(
        public_demo_mode=settings.public_demo_mode,
        registration_enabled=settings.public_demo_registration_enabled,
        max_workspaces_per_user=settings.public_demo_max_workspaces_per_user,
        max_documents_per_workspace=settings.public_demo_max_documents_per_workspace,
        max_tasks_per_workspace=settings.public_demo_max_tasks_per_workspace,
        max_upload_bytes=settings.public_demo_max_upload_bytes,
    )


def ensure_registration_allowed() -> None:
    settings = get_settings()
    if not settings.public_demo_mode:
        return
    if not settings.public_demo_registration_enabled:
        raise PublicDemoAccessError(
            "Public demo registration is currently disabled. Use an operator-provided account or try again later.",
        )


def ensure_workspace_creation_allowed(*, user_id: str) -> None:
    settings = get_settings()
    if not settings.public_demo_mode:
        return

    workspace_count = len(workspace_repository.list_workspaces(user_id=user_id))
    if workspace_count >= settings.public_demo_max_workspaces_per_user:
        raise PublicDemoLimitError(
            f"Public demo limit reached: up to {settings.public_demo_max_workspaces_per_user} workspaces per account.",
        )


def ensure_document_upload_allowed(
    *,
    workspace_id: str,
    user_id: str,
    file_size_bytes: int,
) -> None:
    settings = get_settings()
    if not settings.public_demo_mode:
        return

    if file_size_bytes > settings.public_demo_max_upload_bytes:
        raise PublicDemoUploadLimitError(
            "Public demo upload limit reached: "
            f"files must be {_format_upload_limit(settings.public_demo_max_upload_bytes)} or smaller.",
        )

    document_count = len(
        document_repository.list_documents(workspace_id=workspace_id, user_id=user_id),
    )
    if document_count >= settings.public_demo_max_documents_per_workspace:
        raise PublicDemoLimitError(
            f"Public demo limit reached: up to {settings.public_demo_max_documents_per_workspace} documents per workspace.",
        )


def ensure_task_creation_allowed(*, workspace_id: str, user_id: str) -> None:
    settings = get_settings()
    if not settings.public_demo_mode:
        return

    task_count = len(task_repository.list_workspace_tasks(workspace_id, user_id))
    if task_count >= settings.public_demo_max_tasks_per_workspace:
        raise PublicDemoLimitError(
            f"Public demo limit reached: up to {settings.public_demo_max_tasks_per_workspace} tasks per workspace.",
        )
