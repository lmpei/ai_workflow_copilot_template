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
        return "1 字节"
    return f"{max_upload_bytes} 字节"


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
            "当前已关闭 public demo 自助注册。请使用运营方提供的账号，或稍后再试。",
        )


def ensure_workspace_creation_allowed(*, user_id: str) -> None:
    settings = get_settings()
    if not settings.public_demo_mode:
        return

    workspace_count = len(workspace_repository.list_workspaces(user_id=user_id))
    if workspace_count >= settings.public_demo_max_workspaces_per_user:
        raise PublicDemoLimitError(
            f"已达到 public demo 限额：每个账号最多可创建 {settings.public_demo_max_workspaces_per_user} 个工作区。",
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
            f"已达到 public demo 上传限额：单个文件不能超过 {_format_upload_limit(settings.public_demo_max_upload_bytes)}。",
        )

    document_count = len(
        document_repository.list_documents(workspace_id=workspace_id, user_id=user_id),
    )
    if document_count >= settings.public_demo_max_documents_per_workspace:
        raise PublicDemoLimitError(
            f"已达到 public demo 限额：每个工作区最多可上传 {settings.public_demo_max_documents_per_workspace} 个文档。",
        )


def ensure_task_creation_allowed(*, workspace_id: str, user_id: str) -> None:
    settings = get_settings()
    if not settings.public_demo_mode:
        return

    task_count = len(task_repository.list_workspace_tasks(workspace_id, user_id))
    if task_count >= settings.public_demo_max_tasks_per_workspace:
        raise PublicDemoLimitError(
            f"已达到 public demo 限额：每个工作区最多可创建 {settings.public_demo_max_tasks_per_workspace} 个任务。",
        )
