from arq import create_pool

from app.core.config import get_settings
from app.core.queue import build_redis_settings
from app.models.eval_result import (
    EVAL_RESULT_STATUS_COMPLETED,
    EVAL_RESULT_STATUS_FAILED,
)
from app.models.eval_run import (
    EVAL_RUN_STATUS_COMPLETED,
    EVAL_RUN_STATUS_FAILED,
    EVAL_RUN_STATUS_RUNNING,
)
from app.repositories import eval_repository
from app.services import chat_evaluator_service, retrieval_service, trace_service
from app.services.eval_case_execution_service import (
    EvalExecutionError,
    execute_eval_case,
    resolve_eval_case_question,
    resolve_pass_threshold,
)
from app.services.eval_run_summary_service import build_eval_run_summary
from app.services.scenario_eval_service import (
    ScenarioEvalConfigError,
    build_scenario_summary_fields,
    resolve_scenario_eval_config,
)

EVAL_EXECUTION_JOB_NAME = "run_eval_run"


async def enqueue_eval_run(eval_run_id: str) -> str:
    redis = await create_pool(build_redis_settings())
    job = await redis.enqueue_job(
        EVAL_EXECUTION_JOB_NAME,
        eval_run_id,
        _queue_name=get_settings().task_queue_name,
    )
    close = getattr(redis, "aclose", None)
    if callable(close):
        await close()
    if job is None:
        raise EvalExecutionError("Failed to enqueue eval execution")
    return str(job.job_id)


def run_eval_execution(eval_run_id: str) -> dict[str, object]:
    eval_run = eval_repository.get_eval_run(eval_run_id)
    if eval_run is None:
        raise EvalExecutionError("Eval run not found")

    dataset = eval_repository.get_eval_dataset(eval_run.dataset_id)
    if dataset is None:
        raise EvalExecutionError("Eval dataset not found")

    try:
        scenario_config = resolve_scenario_eval_config(
            workspace_module_type=str(dataset.config_json.get("module_type", "research")),
            config_json=dataset.config_json,
        )
    except ScenarioEvalConfigError as error:
        raise EvalExecutionError(str(error)) from error

    scenario_summary_fields = build_scenario_summary_fields(scenario_config)
    pass_threshold = resolve_pass_threshold(scenario_config)
    cases = eval_repository.list_eval_cases(eval_run.dataset_id)
    total_cases = len(cases)
    completed_cases = 0
    failed_cases = 0
    passed_cases = 0
    score_total = 0.0
    error_messages: list[str] = []

    try:
        running_eval_run = eval_repository.update_eval_run_status(
            eval_run.id,
            next_status=EVAL_RUN_STATUS_RUNNING,
            summary_json={
                **scenario_summary_fields,
                **eval_run.summary_json,
                "total_cases": total_cases,
                "completed_cases": 0,
                "failed_cases": 0,
            },
        )
        if running_eval_run is None:
            raise EvalExecutionError("Eval run not found")

        if not cases:
            raise EvalExecutionError("Eval dataset has no cases")

        for eval_case in cases:
            eval_result = eval_repository.create_eval_result(
                eval_run_id=eval_run.id,
                eval_case_id=eval_case.id,
            )
            try:
                question = resolve_eval_case_question(
                    input_json=eval_case.input_json,
                    scenario_config=scenario_config,
                )
                execution_result = execute_eval_case(
                    eval_run_id=eval_run.id,
                    workspace_id=eval_run.workspace_id,
                    eval_type=eval_run.eval_type,
                    eval_case_id=eval_case.id,
                    case_index=eval_case.case_index,
                    question=question,
                    retriever=retrieval_service.get_retriever(),
                    answer_generator=retrieval_service.get_answer_generator(),
                    fallback_answer=retrieval_service.FALLBACK_ANSWER,
                    record_trace=trace_service.record_trace,
                )
                evaluation_result = chat_evaluator_service.evaluate_retrieval_chat_output(
                    question=question,
                    expected_json=eval_case.expected_json,
                    output_json=execution_result.output_json,
                    pass_threshold=pass_threshold,
                    scenario_context=scenario_summary_fields,
                )
                completed_result = eval_repository.update_eval_result(
                    eval_result.id,
                    next_status=EVAL_RESULT_STATUS_COMPLETED,
                    output_json={
                        **execution_result.output_json,
                        "evaluation": evaluation_result.details_json,
                    },
                    metrics_json={
                        **execution_result.metrics_json,
                        **scenario_summary_fields,
                        "rule_score": evaluation_result.rule_score,
                        "judge_score": evaluation_result.judge_score,
                        "judge_error": evaluation_result.judge_error,
                    },
                    score=evaluation_result.score,
                    passed=evaluation_result.passed,
                )
                if completed_result is None:
                    raise EvalExecutionError("Eval result not found")
                completed_cases += 1
                if evaluation_result.passed is True:
                    passed_cases += 1
                score_total += evaluation_result.score
            except EvalExecutionError as error:
                failed_result = eval_repository.update_eval_result(
                    eval_result.id,
                    next_status=EVAL_RESULT_STATUS_FAILED,
                    output_json={},
                    metrics_json={},
                    error_message=str(error),
                )
                if failed_result is None:
                    raise EvalExecutionError("Eval result not found") from error
                failed_cases += 1
                error_messages.append(str(error))
            finally:
                refreshed = eval_repository.update_eval_run_status(
                    eval_run.id,
                    next_status=EVAL_RUN_STATUS_RUNNING,
                    summary_json=build_eval_run_summary(
                        scenario_summary_fields=scenario_summary_fields,
                        total_cases=total_cases,
                        completed_cases=completed_cases,
                        failed_cases=failed_cases,
                        passed_cases=passed_cases,
                        score_total=score_total,
                    ),
                )
                if refreshed is None:
                    raise EvalExecutionError("Eval run not found")
    except EvalExecutionError as error:
        failed_eval_run = eval_repository.update_eval_run_status(
            eval_run.id,
            next_status=EVAL_RUN_STATUS_FAILED,
            summary_json=build_eval_run_summary(
                scenario_summary_fields=scenario_summary_fields,
                total_cases=total_cases,
                completed_cases=completed_cases,
                failed_cases=failed_cases,
                passed_cases=passed_cases,
                score_total=score_total,
            ),
            error_message=str(error),
        )
        if failed_eval_run is None:
            raise EvalExecutionError("Eval run not found") from error
        raise
    except Exception as error:
        failed_eval_run = eval_repository.update_eval_run_status(
            eval_run.id,
            next_status=EVAL_RUN_STATUS_FAILED,
            summary_json=build_eval_run_summary(
                scenario_summary_fields=scenario_summary_fields,
                total_cases=total_cases,
                completed_cases=completed_cases,
                failed_cases=failed_cases,
                passed_cases=passed_cases,
                score_total=score_total,
            ),
            error_message=str(error),
        )
        if failed_eval_run is None:
            raise EvalExecutionError("Eval run not found") from error
        raise EvalExecutionError(str(error)) from error

    final_summary = build_eval_run_summary(
        scenario_summary_fields=scenario_summary_fields,
        total_cases=total_cases,
        completed_cases=completed_cases,
        failed_cases=failed_cases,
        passed_cases=passed_cases,
        score_total=score_total,
    )
    if failed_cases > 0:
        failed_eval_run = eval_repository.update_eval_run_status(
            eval_run.id,
            next_status=EVAL_RUN_STATUS_FAILED,
            summary_json=final_summary,
            error_message="; ".join(error_messages),
        )
        if failed_eval_run is None:
            raise EvalExecutionError("Eval run not found")
        return {
            "eval_run_id": eval_run.id,
            "status": EVAL_RUN_STATUS_FAILED,
            **final_summary,
        }

    completed_eval_run = eval_repository.update_eval_run_status(
        eval_run.id,
        next_status=EVAL_RUN_STATUS_COMPLETED,
        summary_json=final_summary,
    )
    if completed_eval_run is None:
        raise EvalExecutionError("Eval run not found")
    return {
        "eval_run_id": eval_run.id,
        "status": EVAL_RUN_STATUS_COMPLETED,
        **final_summary,
    }
