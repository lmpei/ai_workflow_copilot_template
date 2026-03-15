from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select

from app.core.database import session_scope
from app.models.eval_case import EvalCase
from app.models.eval_dataset import EvalDataset
from app.models.eval_result import (
    EVAL_RESULT_STATUS_PENDING,
    EvalResult,
    can_transition_eval_result_status,
    is_valid_eval_result_status,
)
from app.models.eval_run import (
    EVAL_RUN_STATUS_COMPLETED,
    EVAL_RUN_STATUS_PENDING,
    EVAL_RUN_STATUS_RUNNING,
    EvalRun,
    can_transition_eval_run_status,
    is_valid_eval_run_status,
)
from app.models.workspace_member import WorkspaceMember


def create_eval_dataset(
    *,
    workspace_id: str,
    name: str,
    eval_type: str,
    created_by: str,
    description: str | None = None,
    config_json: dict[str, object] | None = None,
) -> EvalDataset:
    now = datetime.now(UTC)
    dataset = EvalDataset(
        id=str(uuid4()),
        workspace_id=workspace_id,
        name=name,
        eval_type=eval_type,
        description=description,
        created_by=created_by,
        config_json=config_json or {},
        created_at=now,
        updated_at=now,
    )
    with session_scope() as session:
        session.add(dataset)
        session.flush()
        session.refresh(dataset)
        return dataset


def get_eval_dataset(dataset_id: str) -> EvalDataset | None:
    with session_scope() as session:
        return session.get(EvalDataset, dataset_id)


def get_eval_dataset_for_user(dataset_id: str, user_id: str) -> EvalDataset | None:
    with session_scope() as session:
        statement = (
            select(EvalDataset)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == EvalDataset.workspace_id)
            .where(
                EvalDataset.id == dataset_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        return session.scalar(statement)


def list_workspace_eval_datasets(workspace_id: str, user_id: str) -> list[EvalDataset]:
    with session_scope() as session:
        statement = (
            select(EvalDataset)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == EvalDataset.workspace_id)
            .where(
                EvalDataset.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
            .order_by(EvalDataset.created_at.asc())
        )
        return list(session.scalars(statement))


def create_eval_case(
    *,
    dataset_id: str,
    case_index: int,
    input_json: dict[str, object] | None = None,
    expected_json: dict[str, object] | None = None,
    metadata_json: dict[str, object] | None = None,
) -> EvalCase:
    now = datetime.now(UTC)
    eval_case = EvalCase(
        id=str(uuid4()),
        dataset_id=dataset_id,
        case_index=case_index,
        input_json=input_json or {},
        expected_json=expected_json or {},
        metadata_json=metadata_json or {},
        created_at=now,
        updated_at=now,
    )
    with session_scope() as session:
        session.add(eval_case)
        session.flush()
        session.refresh(eval_case)
        return eval_case


def list_eval_cases(dataset_id: str) -> list[EvalCase]:
    with session_scope() as session:
        statement = (
            select(EvalCase)
            .where(EvalCase.dataset_id == dataset_id)
            .order_by(EvalCase.case_index.asc(), EvalCase.created_at.asc())
        )
        return list(session.scalars(statement))


def create_eval_run(
    *,
    workspace_id: str,
    dataset_id: str,
    eval_type: str,
    created_by: str,
    summary_json: dict[str, object] | None = None,
    status: str = EVAL_RUN_STATUS_PENDING,
) -> EvalRun:
    if not is_valid_eval_run_status(status):
        raise ValueError(f"Unsupported eval run status: {status}")

    now = datetime.now(UTC)
    eval_run = EvalRun(
        id=str(uuid4()),
        workspace_id=workspace_id,
        dataset_id=dataset_id,
        eval_type=eval_type,
        status=status,
        created_by=created_by,
        summary_json=summary_json or {},
        error_message=None,
        created_at=now,
        started_at=now if status == EVAL_RUN_STATUS_RUNNING else None,
        ended_at=None,
    )
    with session_scope() as session:
        session.add(eval_run)
        session.flush()
        session.refresh(eval_run)
        return eval_run


def get_eval_run(eval_run_id: str) -> EvalRun | None:
    with session_scope() as session:
        return session.get(EvalRun, eval_run_id)


def get_eval_run_for_user(eval_run_id: str, user_id: str) -> EvalRun | None:
    with session_scope() as session:
        statement = (
            select(EvalRun)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == EvalRun.workspace_id)
            .where(
                EvalRun.id == eval_run_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        return session.scalar(statement)


def list_workspace_eval_runs(workspace_id: str, user_id: str) -> list[EvalRun]:
    with session_scope() as session:
        statement = (
            select(EvalRun)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == EvalRun.workspace_id)
            .where(
                EvalRun.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
            .order_by(EvalRun.created_at.asc())
        )
        return list(session.scalars(statement))


def update_eval_run_status(
    eval_run_id: str,
    *,
    next_status: str,
    summary_json: dict[str, object] | None = None,
    error_message: str | None = None,
) -> EvalRun | None:
    if not is_valid_eval_run_status(next_status):
        raise ValueError(f"Unsupported eval run status: {next_status}")

    with session_scope() as session:
        eval_run = session.get(EvalRun, eval_run_id)
        if eval_run is None:
            return None

        if not can_transition_eval_run_status(eval_run.status, next_status):
            raise ValueError(
                f"Invalid eval run status transition: {eval_run.status} -> {next_status}",
            )

        if next_status == EVAL_RUN_STATUS_COMPLETED:
            has_cases = session.scalar(
                select(EvalCase.id).where(EvalCase.dataset_id == eval_run.dataset_id).limit(1)
            )
            if has_cases is None:
                raise ValueError("Cannot complete eval run without eval cases")

        eval_run.status = next_status
        now = datetime.now(UTC)
        if next_status == EVAL_RUN_STATUS_RUNNING and eval_run.started_at is None:
            eval_run.started_at = now
        if next_status in {"completed", "failed"}:
            eval_run.ended_at = now
        if summary_json is not None:
            eval_run.summary_json = summary_json
        if error_message is not None:
            eval_run.error_message = error_message
        elif next_status != "failed":
            eval_run.error_message = None

        session.add(eval_run)
        session.flush()
        session.refresh(eval_run)
        return eval_run


def create_eval_result(
    *,
    eval_run_id: str,
    eval_case_id: str,
    status: str = EVAL_RESULT_STATUS_PENDING,
    output_json: dict[str, object] | None = None,
    metrics_json: dict[str, object] | None = None,
    score: float | None = None,
    passed: bool | None = None,
    error_message: str | None = None,
) -> EvalResult:
    if not is_valid_eval_result_status(status):
        raise ValueError(f"Unsupported eval result status: {status}")

    now = datetime.now(UTC)
    eval_result = EvalResult(
        id=str(uuid4()),
        eval_run_id=eval_run_id,
        eval_case_id=eval_case_id,
        status=status,
        output_json=output_json or {},
        metrics_json=metrics_json or {},
        score=score,
        passed=passed,
        error_message=error_message,
        created_at=now,
        updated_at=now,
    )
    with session_scope() as session:
        session.add(eval_result)
        session.flush()
        session.refresh(eval_result)
        return eval_result


def list_eval_run_results(eval_run_id: str) -> list[EvalResult]:
    with session_scope() as session:
        statement = (
            select(EvalResult)
            .where(EvalResult.eval_run_id == eval_run_id)
            .order_by(EvalResult.created_at.asc())
        )
        return list(session.scalars(statement))


def update_eval_result(
    eval_result_id: str,
    *,
    next_status: str,
    output_json: dict[str, object] | None = None,
    metrics_json: dict[str, object] | None = None,
    score: float | None = None,
    passed: bool | None = None,
    error_message: str | None = None,
) -> EvalResult | None:
    if not is_valid_eval_result_status(next_status):
        raise ValueError(f"Unsupported eval result status: {next_status}")

    with session_scope() as session:
        eval_result = session.get(EvalResult, eval_result_id)
        if eval_result is None:
            return None

        if not can_transition_eval_result_status(eval_result.status, next_status):
            raise ValueError(
                f"Invalid eval result status transition: {eval_result.status} -> {next_status}",
            )

        eval_result.status = next_status
        eval_result.updated_at = datetime.now(UTC)
        if output_json is not None:
            eval_result.output_json = output_json
        if metrics_json is not None:
            eval_result.metrics_json = metrics_json
        if score is not None:
            eval_result.score = score
        if passed is not None:
            eval_result.passed = passed
        if error_message is not None:
            eval_result.error_message = error_message
        elif next_status != "failed":
            eval_result.error_message = None

        session.add(eval_result)
        session.flush()
        session.refresh(eval_result)
        return eval_result
