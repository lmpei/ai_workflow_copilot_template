from uuid import uuid4

import pytest

from app.core.database import reset_database_for_tests
from app.models.eval_result import EVAL_RESULT_STATUS_PENDING
from app.models.eval_run import EVAL_RUN_STATUS_PENDING, EVAL_RUN_STATUS_RUNNING
from app.repositories.eval_repository import (
    create_eval_case,
    create_eval_dataset,
    create_eval_result,
    create_eval_run,
    get_eval_dataset,
    get_eval_dataset_for_user,
    get_eval_run,
    get_eval_run_for_user,
    list_eval_cases,
    list_eval_run_results,
    list_workspace_eval_datasets,
    list_workspace_eval_runs,
    update_eval_result,
    update_eval_run_status,
)
from app.repositories.user_repository import create_user
from app.repositories.workspace_repository import create_workspace
from app.schemas.workspace import WorkspaceCreate


@pytest.fixture(autouse=True)
def reset_database() -> None:
    reset_database_for_tests()



def _create_workspace_fixture() -> tuple[str, str]:
    unique_suffix = uuid4().hex
    user = create_user(
        email=f"phase4-owner-{unique_suffix}@example.com",
        password_hash="not-used-in-this-test",
        name="Phase 4 Owner",
    )
    workspace = create_workspace(
        WorkspaceCreate(name="Phase 4 Workspace", type="research"),
        owner_id=user.id,
    )
    return user.id, workspace.id



def test_eval_repository_persists_datasets_cases_runs_and_results() -> None:
    user_id, workspace_id = _create_workspace_fixture()

    dataset = create_eval_dataset(
        workspace_id=workspace_id,
        name="Grounded Chat Dataset",
        eval_type="retrieval_chat",
        created_by=user_id,
        config_json={"mode": "rag"},
    )
    first_case = create_eval_case(
        dataset_id=dataset.id,
        case_index=0,
        input_json={"question": "Who owns Apollo?"},
        expected_json={"answer_contains": ["Alice"]},
    )
    second_case = create_eval_case(
        dataset_id=dataset.id,
        case_index=1,
        input_json={"question": "How many milestones are there?"},
        expected_json={"answer_contains": ["three"]},
        metadata_json={"document_id": "doc-1"},
    )

    eval_run = create_eval_run(
        workspace_id=workspace_id,
        dataset_id=dataset.id,
        eval_type=dataset.eval_type,
        created_by=user_id,
    )
    running_run = update_eval_run_status(eval_run.id, next_status=EVAL_RUN_STATUS_RUNNING)
    first_result = create_eval_result(
        eval_run_id=eval_run.id,
        eval_case_id=first_case.id,
    )
    completed_result = update_eval_result(
        first_result.id,
        next_status="completed",
        output_json={"answer": "Alice owns Project Apollo."},
        metrics_json={"latency_ms": 1200},
        score=1.0,
        passed=True,
    )
    completed_run = update_eval_run_status(
        eval_run.id,
        next_status="completed",
        summary_json={"total_cases": 2, "completed_cases": 1},
    )

    assert get_eval_dataset(dataset.id) is not None
    assert get_eval_dataset_for_user(dataset.id, user_id) is not None
    assert [item.id for item in list_workspace_eval_datasets(workspace_id, user_id)] == [dataset.id]
    assert [item.id for item in list_eval_cases(dataset.id)] == [first_case.id, second_case.id]
    assert eval_run.status == EVAL_RUN_STATUS_PENDING
    assert running_run is not None and running_run.started_at is not None
    assert get_eval_run(eval_run.id) is not None
    assert get_eval_run_for_user(eval_run.id, user_id) is not None
    assert [item.id for item in list_workspace_eval_runs(workspace_id, user_id)] == [eval_run.id]
    assert first_result.status == EVAL_RESULT_STATUS_PENDING
    assert completed_result is not None and completed_result.passed is True
    assert completed_result.metrics_json == {"latency_ms": 1200}
    assert [item.id for item in list_eval_run_results(eval_run.id)] == [first_result.id]
    assert completed_run is not None
    assert completed_run.status == "completed"
    assert completed_run.summary_json == {"total_cases": 2, "completed_cases": 1}



def test_eval_repository_rejects_invalid_transitions_and_empty_dataset_completion() -> None:
    user_id, workspace_id = _create_workspace_fixture()
    dataset = create_eval_dataset(
        workspace_id=workspace_id,
        name="Empty Dataset",
        eval_type="retrieval_chat",
        created_by=user_id,
    )
    eval_run = create_eval_run(
        workspace_id=workspace_id,
        dataset_id=dataset.id,
        eval_type=dataset.eval_type,
        created_by=user_id,
    )

    running_run = update_eval_run_status(eval_run.id, next_status=EVAL_RUN_STATUS_RUNNING)
    assert running_run is not None

    with pytest.raises(ValueError, match="Cannot complete eval run without eval cases"):
        update_eval_run_status(eval_run.id, next_status="completed")

    with pytest.raises(ValueError, match="Invalid eval run status transition"):
        update_eval_run_status(eval_run.id, next_status=EVAL_RUN_STATUS_PENDING)

    with pytest.raises(ValueError, match="Unsupported eval run status"):
        update_eval_run_status(eval_run.id, next_status="queued")



def test_eval_results_reject_invalid_status_transitions() -> None:
    user_id, workspace_id = _create_workspace_fixture()
    dataset = create_eval_dataset(
        workspace_id=workspace_id,
        name="Result Dataset",
        eval_type="retrieval_chat",
        created_by=user_id,
    )
    eval_case = create_eval_case(dataset_id=dataset.id, case_index=0)
    eval_run = create_eval_run(
        workspace_id=workspace_id,
        dataset_id=dataset.id,
        eval_type=dataset.eval_type,
        created_by=user_id,
    )
    eval_result = create_eval_result(eval_run_id=eval_run.id, eval_case_id=eval_case.id)

    failed_result = update_eval_result(
        eval_result.id,
        next_status="failed",
        error_message="Judge unavailable",
    )
    assert failed_result is not None
    assert failed_result.error_message == "Judge unavailable"

    with pytest.raises(ValueError, match="Invalid eval result status transition"):
        update_eval_result(eval_result.id, next_status="completed")

    with pytest.raises(ValueError, match="Unsupported eval result status"):
        update_eval_result(eval_result.id, next_status="running")

