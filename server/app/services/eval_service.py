from app.models.workspace import Workspace
from app.repositories import eval_repository, workspace_repository
from app.schemas.eval import (
    SUPPORTED_EVAL_TYPES,
    EvalDatasetCreate,
    EvalDatasetResponse,
    EvalResultResponse,
    EvalRunCreate,
    EvalRunResponse,
)
from app.services.eval_execution_service import EvalExecutionError, enqueue_eval_run
from app.services.scenario_eval_service import (
    ScenarioEvalConfigError,
    build_scenario_metadata_json,
    build_scenario_summary_fields,
    resolve_scenario_eval_config,
)


class EvalAccessError(Exception):
    pass


class EvalValidationError(Exception):
    pass


class EvalQueueError(Exception):
    pass


def _get_workspace_or_raise(*, workspace_id: str, user_id: str) -> Workspace:
    workspace = workspace_repository.get_workspace(workspace_id=workspace_id, user_id=user_id)
    if workspace is None:
        raise EvalAccessError("Workspace not found")
    return workspace


def _validate_eval_type(eval_type: str) -> None:
    if eval_type not in SUPPORTED_EVAL_TYPES:
        raise EvalValidationError(f"Unsupported eval type: {eval_type}")


def create_eval_dataset(
    *,
    workspace_id: str,
    user_id: str,
    payload: EvalDatasetCreate,
) -> EvalDatasetResponse:
    workspace = _get_workspace_or_raise(workspace_id=workspace_id, user_id=user_id)
    _validate_eval_type(payload.eval_type)

    try:
        scenario_config = resolve_scenario_eval_config(
            workspace_module_type=workspace.module_type,
            config_json=payload.config_json,
        )
    except ScenarioEvalConfigError as error:
        raise EvalValidationError(str(error)) from error

    dataset = eval_repository.create_eval_dataset(
        workspace_id=workspace_id,
        name=payload.name,
        eval_type=payload.eval_type,
        created_by=user_id,
        description=payload.description,
        config_json=scenario_config,
    )
    cases = [
        eval_repository.create_eval_case(
            dataset_id=dataset.id,
            case_index=index,
            input_json=eval_case.input_json,
            expected_json=eval_case.expected_json,
            metadata_json=build_scenario_metadata_json(
                scenario_config=scenario_config,
                metadata_json=eval_case.metadata_json,
            ),
        )
        for index, eval_case in enumerate(payload.cases)
    ]
    return EvalDatasetResponse.from_model(dataset, cases=cases)


def list_workspace_eval_datasets(*, workspace_id: str, user_id: str) -> list[EvalDatasetResponse]:
    _get_workspace_or_raise(workspace_id=workspace_id, user_id=user_id)
    datasets = eval_repository.list_workspace_eval_datasets(workspace_id, user_id)
    return [
        EvalDatasetResponse.from_model(
            dataset,
            cases=eval_repository.list_eval_cases(dataset.id),
        )
        for dataset in datasets
    ]


async def create_eval_run(
    *,
    workspace_id: str,
    user_id: str,
    payload: EvalRunCreate,
) -> EvalRunResponse:
    workspace = _get_workspace_or_raise(workspace_id=workspace_id, user_id=user_id)
    dataset = eval_repository.get_eval_dataset_for_user(payload.dataset_id, user_id)
    if dataset is None or dataset.workspace_id != workspace_id:
        raise EvalAccessError("Eval dataset not found")

    try:
        scenario_summary_fields = build_scenario_summary_fields(
            resolve_scenario_eval_config(
                workspace_module_type=workspace.module_type,
                config_json=dataset.config_json,
            )
        )
    except ScenarioEvalConfigError as error:
        raise EvalValidationError(str(error)) from error

    eval_run = eval_repository.create_eval_run(
        workspace_id=workspace_id,
        dataset_id=dataset.id,
        eval_type=dataset.eval_type,
        created_by=user_id,
        summary_json={
            **scenario_summary_fields,
            "total_cases": len(eval_repository.list_eval_cases(dataset.id)),
            "completed_cases": 0,
            "failed_cases": 0,
        },
    )
    try:
        await enqueue_eval_run(eval_run.id)
    except EvalExecutionError as error:
        failed_eval_run = eval_repository.update_eval_run_status(
            eval_run.id,
            next_status="failed",
            summary_json=eval_run.summary_json,
            error_message=str(error),
        )
        if failed_eval_run is None:
            raise EvalQueueError("Failed to enqueue eval run") from error
        raise EvalQueueError(str(error)) from error
    return EvalRunResponse.from_model(eval_run)


def get_eval_run(*, eval_run_id: str, user_id: str) -> EvalRunResponse | None:
    eval_run = eval_repository.get_eval_run_for_user(eval_run_id, user_id)
    if eval_run is None:
        return None
    return EvalRunResponse.from_model(eval_run)


def list_eval_run_results(*, eval_run_id: str, user_id: str) -> list[EvalResultResponse]:
    eval_run = eval_repository.get_eval_run_for_user(eval_run_id, user_id)
    if eval_run is None:
        raise EvalAccessError("Eval run not found")
    results = eval_repository.list_eval_run_results(eval_run_id)
    return [EvalResultResponse.from_model(result) for result in results]
