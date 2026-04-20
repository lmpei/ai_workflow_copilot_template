from copy import deepcopy

from pydantic import ValidationError

from app.core.runtime_control import (
    build_retry_attempt_control,
    build_retry_created_control,
    get_linked_retry_target_id,
    is_cancel_recorded,
    resolve_cancel_transition,
)
from app.repositories import task_repository, workspace_repository
from app.schemas.scenario import (
    MODULE_TYPE_JOB,
    MODULE_TYPE_RESEARCH,
    MODULE_TYPE_SUPPORT,
    get_scenario_task_module_type,
)
from app.schemas.task import TaskControlRequest, TaskCreate, TaskResponse
from app.services.job_assistant_service import (
    JobAssistantContractError,
    normalize_job_task_input,
    validate_job_task_contract,
)
from app.services.research_assistant_service import (
    ResearchAssistantContractError,
    normalize_research_task_input,
    validate_research_task_contract,
)
from app.services.support_copilot_service import (
    SupportCopilotContractError,
    normalize_support_task_input,
    validate_support_task_contract,
)
from app.services.task_execution_service import TaskExecutionError, enqueue_task_execution

MODULE_CONTRACT_VALIDATORS = {
    MODULE_TYPE_RESEARCH: validate_research_task_contract,
    MODULE_TYPE_SUPPORT: validate_support_task_contract,
    MODULE_TYPE_JOB: validate_job_task_contract,
}
MODULE_INPUT_NORMALIZERS = {
    MODULE_TYPE_RESEARCH: normalize_research_task_input,
    MODULE_TYPE_SUPPORT: normalize_support_task_input,
    MODULE_TYPE_JOB: normalize_job_task_input,
}
MODULE_CONTRACT_ERRORS = (
    ResearchAssistantContractError,
    SupportCopilotContractError,
    JobAssistantContractError,
)
MODULE_VALIDATION_ERRORS = MODULE_CONTRACT_ERRORS + (ValidationError,)
TASK_CANCELLED_ERROR_MESSAGE = "任务已被操作员取消"


class TaskAccessError(Exception):
    pass


class TaskValidationError(Exception):
    pass


class TaskQueueError(Exception):
    pass


class TaskControlError(Exception):
    pass


def _resolve_task_module_type(task_type: str) -> str:
    try:
        return get_scenario_task_module_type(task_type)
    except ValueError as error:
        raise TaskValidationError(str(error)) from error


def _normalize_task_input(
    *,
    workspace_module_type: str,
    task_type: str,
    input_json: dict[str, object],
) -> dict[str, object]:
    task_module_type = _resolve_task_module_type(task_type)
    validate_contract = MODULE_CONTRACT_VALIDATORS[task_module_type]
    normalize_input = MODULE_INPUT_NORMALIZERS[task_module_type]
    validate_contract(
        workspace_module_type=workspace_module_type,
        task_type=task_type,
    )
    return normalize_input(input_json)


def _validate_research_task_lineage(
    *,
    workspace_id: str,
    user_id: str,
    normalized_input: dict[str, object],
) -> None:
    research_asset_id = normalized_input.get("research_asset_id")
    if isinstance(research_asset_id, str) and research_asset_id:
        from app.repositories import research_asset_repository

        asset = research_asset_repository.get_research_asset_for_user(research_asset_id, user_id)
        if asset is None or asset.workspace_id != workspace_id:
            raise TaskValidationError("当前工作区中未找到对应的研究资产")

    parent_task_id = normalized_input.get("parent_task_id")
    if isinstance(parent_task_id, str) and parent_task_id:
        parent_task = task_repository.get_task_for_user(parent_task_id, user_id)
        if parent_task is None or parent_task.workspace_id != workspace_id:
            raise TaskValidationError("当前工作区中未找到父级研究任务")
        if _resolve_task_module_type(parent_task.task_type) != MODULE_TYPE_RESEARCH:
            raise TaskValidationError("父任务必须是已完成的 Research 任务")
        if parent_task.status != "done":
            raise TaskValidationError("父级研究任务必须先完成后才能继续跟进")
        result = parent_task.output_json.get("result")
        if not isinstance(result, dict) or result.get("module_type") != MODULE_TYPE_RESEARCH:
            raise TaskValidationError("父级研究任务不包含结构化 Research 结果")

        if isinstance(research_asset_id, str) and research_asset_id:
            from app.repositories import research_asset_repository

            asset_revision = research_asset_repository.get_research_asset_revision_by_task_id(parent_task_id)
            if asset_revision is not None and asset_revision.research_asset_id != research_asset_id:
                raise TaskValidationError("父级研究任务关联的是另一个 Research 资产")


def _validate_support_task_lineage(
    *,
    workspace_id: str,
    user_id: str,
    normalized_input: dict[str, object],
) -> None:
    parent_task_id = normalized_input.get("parent_task_id")
    if not isinstance(parent_task_id, str) or not parent_task_id:
        return

    parent_task = task_repository.get_task_for_user(parent_task_id, user_id)
    if parent_task is None or parent_task.workspace_id != workspace_id:
        raise TaskValidationError("当前工作区中未找到父级 Support 任务")
    if _resolve_task_module_type(parent_task.task_type) != MODULE_TYPE_SUPPORT:
        raise TaskValidationError("父任务必须是已完成的 Support 任务")
    if parent_task.status != "done":
        raise TaskValidationError("父级 Support 任务必须先完成后才能继续跟进")

    result = parent_task.output_json.get("result")
    if not isinstance(result, dict) or result.get("module_type") != MODULE_TYPE_SUPPORT:
        raise TaskValidationError("父级 Support 任务不包含结构化 Support 结果")


def _validate_job_task_comparison(
    *,
    workspace_id: str,
    user_id: str,
    task_type: str,
    normalized_input: dict[str, object],
) -> None:
    comparison_task_ids = normalized_input.get("comparison_task_ids")
    if not isinstance(comparison_task_ids, list) or len(comparison_task_ids) == 0:
        return

    if task_type != "resume_match":
        raise TaskValidationError("只有 resume_match 任务支持 comparison_task_ids")
    if len(comparison_task_ids) < 2:
        raise TaskValidationError("短名单评审至少需要两个对比招聘任务")

    normalized_target_role = normalized_input.get("target_role")
    target_role_key = normalized_target_role.strip().casefold() if isinstance(normalized_target_role, str) and normalized_target_role.strip() else None

    for comparison_task_id in comparison_task_ids:
        if not isinstance(comparison_task_id, str) or not comparison_task_id:
            raise TaskValidationError("对比招聘任务 ID 必须是非空字符串")
        comparison_task = task_repository.get_task_for_user(comparison_task_id, user_id)
        if comparison_task is None or comparison_task.workspace_id != workspace_id:
            raise TaskValidationError("当前工作区中未找到对比招聘任务")
        if _resolve_task_module_type(comparison_task.task_type) != MODULE_TYPE_JOB:
            raise TaskValidationError("对比任务必须是已完成的 Job 评审任务")
        if comparison_task.task_type != "resume_match":
            raise TaskValidationError("对比任务必须是已完成的 Job resume_match 任务")
        if comparison_task.status != "done":
            raise TaskValidationError("对比招聘任务必须先完成后才能做短名单评审")

        result = comparison_task.output_json.get("result")
        if not isinstance(result, dict) or result.get("module_type") != MODULE_TYPE_JOB:
            raise TaskValidationError("对比招聘任务不包含结构化 Job 结果")
        input_payload = result.get("input")
        if not isinstance(input_payload, dict):
            continue
        nested_comparison_ids = input_payload.get("comparison_task_ids")
        if isinstance(nested_comparison_ids, list) and len(nested_comparison_ids) > 0:
            raise TaskValidationError(
                "对比招聘任务必须是单个候选人的评审结果，不能引用已有短名单",
            )
        comparison_target_role = input_payload.get("target_role")
        comparison_role_key = (
            comparison_target_role.strip().casefold()
            if isinstance(comparison_target_role, str) and comparison_target_role.strip()
            else None
        )
        if target_role_key is not None and comparison_role_key is not None and target_role_key != comparison_role_key:
            raise TaskValidationError("对比招聘任务必须与当前 target_role 一致")


def _get_workspace_or_raise(*, workspace_id: str, user_id: str):
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise TaskAccessError("未找到工作区")
    return workspace


def _get_task_or_raise(*, task_id: str, user_id: str):
    task = task_repository.get_task_for_user(task_id, user_id)
    if task is None:
        raise TaskAccessError("未找到任务")
    return task


async def create_task(
    *,
    workspace_id: str,
    user_id: str,
    payload: TaskCreate,
) -> TaskResponse:
    workspace = _get_workspace_or_raise(workspace_id=workspace_id, user_id=user_id)
    task_module_type = _resolve_task_module_type(payload.task_type)

    try:
        normalized_input = _normalize_task_input(
            workspace_module_type=workspace.module_type,
            task_type=payload.task_type,
            input_json=payload.input,
        )
    except MODULE_VALIDATION_ERRORS as error:
        raise TaskValidationError(str(error)) from error

    if task_module_type == MODULE_TYPE_RESEARCH:
        _validate_research_task_lineage(
            workspace_id=workspace_id,
            user_id=user_id,
            normalized_input=normalized_input,
        )
    elif task_module_type == MODULE_TYPE_SUPPORT:
        _validate_support_task_lineage(
            workspace_id=workspace_id,
            user_id=user_id,
            normalized_input=normalized_input,
        )
    elif task_module_type == MODULE_TYPE_JOB:
        _validate_job_task_comparison(
            workspace_id=workspace_id,
            user_id=user_id,
            task_type=payload.task_type,
            normalized_input=normalized_input,
        )

    task = task_repository.create_task(
        workspace_id=workspace_id,
        task_type=payload.task_type,
        created_by=user_id,
        input_json=normalized_input,
    )

    try:
        await enqueue_task_execution(task.id)
    except TaskExecutionError as error:
        failed_task = task_repository.update_task_status(
            task.id,
            next_status="failed",
            error_message=str(error),
        )
        if failed_task is None:
            raise TaskQueueError("任务执行入队失败") from error
        raise TaskQueueError(str(error)) from error

    return TaskResponse.from_model(task)


def get_task(*, task_id: str, user_id: str) -> TaskResponse | None:
    task = task_repository.get_task_for_user(task_id, user_id)
    if task is None:
        return None
    return TaskResponse.from_model(task)


def list_workspace_tasks(*, workspace_id: str, user_id: str) -> list[TaskResponse]:
    _get_workspace_or_raise(workspace_id=workspace_id, user_id=user_id)
    tasks = task_repository.list_workspace_tasks(workspace_id, user_id)
    return [TaskResponse.from_model(task) for task in tasks]


def cancel_task(
    *,
    task_id: str,
    user_id: str,
    payload: TaskControlRequest | None = None,
) -> TaskResponse:
    task = _get_task_or_raise(task_id=task_id, user_id=user_id)
    reason = payload.reason if payload is not None else None

    if is_cancel_recorded(task.control_json):
        return TaskResponse.from_model(task)

    try:
        cancel_transition = resolve_cancel_transition(
            current_status=task.status,
            current_control_json=task.control_json,
            user_id=user_id,
            reason=reason,
            cancelled_error_message=TASK_CANCELLED_ERROR_MESSAGE,
        )
    except ValueError as error:
        raise TaskControlError(str(error).replace("runtime items", "tasks")) from error

    updated_task = task_repository.update_task_status(
        task.id,
        next_status=cancel_transition.next_status,
        control_json=cancel_transition.control_json,
        error_message=cancel_transition.error_message,
    )

    if updated_task is None:
        raise TaskAccessError("未找到任务")
    return TaskResponse.from_model(updated_task)


async def retry_task(
    *,
    task_id: str,
    user_id: str,
    payload: TaskControlRequest | None = None,
) -> TaskResponse:
    task = _get_task_or_raise(task_id=task_id, user_id=user_id)
    reason = payload.reason if payload is not None else None

    if task.status != "failed":
        raise TaskControlError("只有失败的任务才能重试")

    existing_retry_task_id = get_linked_retry_target_id(
        task.control_json,
        target_id_key="target_task_id",
    )
    if isinstance(existing_retry_task_id, str) and existing_retry_task_id:
        existing_retry_task = task_repository.get_task_for_user(existing_retry_task_id, user_id)
        if existing_retry_task is not None:
            return TaskResponse.from_model(existing_retry_task)

    retry_task_record = task_repository.create_task(
        workspace_id=task.workspace_id,
        task_type=task.task_type,
        created_by=user_id,
        input_json=deepcopy(task.input_json),
        control_json=build_retry_attempt_control(
            user_id=user_id,
            source_id_key="source_task_id",
            source_id=task.id,
            reason=reason,
        ),
    )

    try:
        await enqueue_task_execution(retry_task_record.id)
    except TaskExecutionError as error:
        failed_retry_task = task_repository.update_task_status(
            retry_task_record.id,
            next_status="failed",
            control_json=build_retry_attempt_control(
                user_id=user_id,
                source_id_key="source_task_id",
                source_id=task.id,
                reason=reason,
                extra_json={"retry_enqueue_failed": True},
            ),
            error_message=str(error),
        )
        if failed_retry_task is None:
            raise TaskQueueError("重试任务执行入队失败") from error
        raise TaskQueueError(str(error)) from error

    updated_original = task_repository.update_task_status(
        task.id,
        next_status=task.status,
        control_json=build_retry_created_control(
            current_control_json=task.control_json,
            user_id=user_id,
            target_id_key="target_task_id",
            target_id=retry_task_record.id,
            reason=reason,
        ),
    )
    if updated_original is None:
        raise TaskAccessError("未找到任务")

    return TaskResponse.from_model(retry_task_record)
