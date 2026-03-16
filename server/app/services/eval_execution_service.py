from dataclasses import dataclass
from datetime import UTC, datetime

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
from app.services.retrieval_service import (
    ChatProcessingError,
    GeneratedAnswer,
    RetrievedChunk,
)
from app.services.scenario_eval_service import (
    ScenarioEvalConfigError,
    build_scenario_summary_fields,
    resolve_scenario_eval_config,
    resolve_scenario_eval_prompt,
)

EVAL_EXECUTION_JOB_NAME = "run_eval_run"


class EvalExecutionError(Exception):
    pass


@dataclass(slots=True)
class EvalCaseExecutionResult:
    output_json: dict[str, object]
    metrics_json: dict[str, object]



def _serialize_retrieved_chunks(chunks: list[RetrievedChunk]) -> list[dict[str, object]]:
    return [
        {
            "document_id": chunk.document_id,
            "chunk_id": chunk.chunk_id,
            "document_title": chunk.document_title,
            "chunk_index": chunk.chunk_index,
            "snippet": chunk.snippet,
        }
        for chunk in chunks
    ]



def _execute_retrieval_chat_case(
    *,
    workspace_id: str,
    eval_run_id: str,
    eval_case_id: str,
    case_index: int,
    question: str,
) -> EvalCaseExecutionResult:
    started_at = datetime.now(UTC)
    retrieved_chunks: list[RetrievedChunk] = []
    prompt = ""
    answer = ""
    token_input = 0
    token_output = 0
    estimated_cost = 0.0

    try:
        retriever = retrieval_service.get_retriever()
        answer_generator = retrieval_service.get_answer_generator()
        retrieved_chunks = retriever.retrieve(workspace_id=workspace_id, question=question)
        serialized_sources = _serialize_retrieved_chunks(retrieved_chunks)

        if retrieved_chunks:
            generated: GeneratedAnswer = answer_generator.generate_answer(
                question=question,
                retrieved_chunks=retrieved_chunks,
            )
            answer = generated.answer
            prompt = generated.prompt
            token_input = generated.token_input
            token_output = generated.token_output
            estimated_cost = generated.estimated_cost
        else:
            answer = retrieval_service.FALLBACK_ANSWER

        latency_ms = max(int((datetime.now(UTC) - started_at).total_seconds() * 1000), 0)
        trace_id = trace_service.record_trace(
            workspace_id=workspace_id,
            trace_type="eval",
            eval_run_id=eval_run_id,
            request_json={
                "eval_case_id": eval_case_id,
                "question": question,
            },
            response_json={
                "answer": answer,
                "sources": serialized_sources,
                "error": None,
            },
            metadata_json={
                "case_index": case_index,
                "prompt": prompt,
                "retrieved_chunks": serialized_sources,
            },
            latency_ms=latency_ms,
            token_input=token_input,
            token_output=token_output,
            estimated_cost=estimated_cost,
        )
        return EvalCaseExecutionResult(
            output_json={
                "answer": answer,
                "sources": serialized_sources,
                "trace_id": trace_id,
            },
            metrics_json={
                "latency_ms": latency_ms,
                "token_input": token_input,
                "token_output": token_output,
                "estimated_cost": estimated_cost,
                "retrieval_hit": len(serialized_sources) > 0,
            },
        )
    except ChatProcessingError as error:
        latency_ms = max(int((datetime.now(UTC) - started_at).total_seconds() * 1000), 0)
        serialized_sources = _serialize_retrieved_chunks(retrieved_chunks)
        trace_service.record_trace(
            workspace_id=workspace_id,
            trace_type="eval",
            eval_run_id=eval_run_id,
            request_json={
                "eval_case_id": eval_case_id,
                "question": question,
            },
            response_json={
                "answer": answer,
                "sources": serialized_sources,
                "error": str(error),
            },
            metadata_json={
                "case_index": case_index,
                "prompt": prompt,
                "retrieved_chunks": serialized_sources,
            },
            error_message=str(error),
            latency_ms=latency_ms,
            token_input=token_input,
            token_output=token_output,
            estimated_cost=estimated_cost,
        )
        raise EvalExecutionError(str(error)) from error
    except Exception as error:
        latency_ms = max(int((datetime.now(UTC) - started_at).total_seconds() * 1000), 0)
        serialized_sources = _serialize_retrieved_chunks(retrieved_chunks)
        trace_service.record_trace(
            workspace_id=workspace_id,
            trace_type="eval",
            eval_run_id=eval_run_id,
            request_json={
                "eval_case_id": eval_case_id,
                "question": question,
            },
            response_json={
                "answer": answer,
                "sources": serialized_sources,
                "error": str(error),
            },
            metadata_json={
                "case_index": case_index,
                "prompt": prompt,
                "retrieved_chunks": serialized_sources,
            },
            error_message=str(error),
            latency_ms=latency_ms,
            token_input=token_input,
            token_output=token_output,
            estimated_cost=estimated_cost,
        )
        raise EvalExecutionError(str(error)) from error



def _execute_eval_case(
    *,
    eval_run_id: str,
    workspace_id: str,
    eval_type: str,
    eval_case_id: str,
    case_index: int,
    question: str,
) -> EvalCaseExecutionResult:
    if eval_type != "retrieval_chat":
        raise EvalExecutionError(f"Unsupported eval type: {eval_type}")

    return _execute_retrieval_chat_case(
        workspace_id=workspace_id,
        eval_run_id=eval_run_id,
        eval_case_id=eval_case_id,
        case_index=case_index,
        question=question,
    )


def _resolve_eval_case_question(
    *,
    input_json: dict[str, object],
    scenario_config: dict[str, object],
) -> str:
    try:
        return resolve_scenario_eval_prompt(
            input_json=input_json,
            scenario_config=scenario_config,
        )
    except ScenarioEvalConfigError as error:
        raise EvalExecutionError(str(error)) from error


def _resolve_pass_threshold(scenario_config: dict[str, object]) -> float:
    pass_threshold = scenario_config.get("pass_threshold")
    if not isinstance(pass_threshold, int | float):
        raise EvalExecutionError("Scenario eval config must include a numeric pass_threshold")
    return float(pass_threshold)


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
    pass_threshold = _resolve_pass_threshold(scenario_config)
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
                question = _resolve_eval_case_question(
                    input_json=eval_case.input_json,
                    scenario_config=scenario_config,
                )
                execution_result = _execute_eval_case(
                    eval_run_id=eval_run.id,
                    workspace_id=eval_run.workspace_id,
                    eval_type=eval_run.eval_type,
                    eval_case_id=eval_case.id,
                    case_index=eval_case.case_index,
                    question=question,
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
                    summary_json={
                        **scenario_summary_fields,
                        "total_cases": total_cases,
                        "completed_cases": completed_cases,
                        "failed_cases": failed_cases,
                        "passed_cases": passed_cases,
                        "avg_score": round(score_total / completed_cases, 4)
                        if completed_cases > 0
                        else 0.0,
                        "pass_rate": round(passed_cases / total_cases, 4)
                        if total_cases > 0
                        else 0.0,
                    },
                )
                if refreshed is None:
                    raise EvalExecutionError("Eval run not found")
    except EvalExecutionError as error:
        failed_eval_run = eval_repository.update_eval_run_status(
            eval_run.id,
            next_status=EVAL_RUN_STATUS_FAILED,
            summary_json={
                **scenario_summary_fields,
                "total_cases": total_cases,
                "completed_cases": completed_cases,
                "failed_cases": failed_cases,
                "passed_cases": passed_cases,
                "avg_score": round(score_total / completed_cases, 4)
                if completed_cases > 0
                else 0.0,
                "pass_rate": round(passed_cases / total_cases, 4)
                if total_cases > 0
                else 0.0,
            },
            error_message=str(error),
        )
        if failed_eval_run is None:
            raise EvalExecutionError("Eval run not found") from error
        raise
    except Exception as error:
        failed_eval_run = eval_repository.update_eval_run_status(
            eval_run.id,
            next_status=EVAL_RUN_STATUS_FAILED,
            summary_json={
                **scenario_summary_fields,
                "total_cases": total_cases,
                "completed_cases": completed_cases,
                "failed_cases": failed_cases,
                "passed_cases": passed_cases,
                "avg_score": round(score_total / completed_cases, 4)
                if completed_cases > 0
                else 0.0,
                "pass_rate": round(passed_cases / total_cases, 4)
                if total_cases > 0
                else 0.0,
            },
            error_message=str(error),
        )
        if failed_eval_run is None:
            raise EvalExecutionError("Eval run not found") from error
        raise EvalExecutionError(str(error)) from error

    final_summary: dict[str, object] = {
        **scenario_summary_fields,
        "total_cases": total_cases,
        "completed_cases": completed_cases,
        "failed_cases": failed_cases,
        "passed_cases": passed_cases,
        "avg_score": round(score_total / completed_cases, 4) if completed_cases > 0 else 0.0,
        "pass_rate": round(passed_cases / total_cases, 4) if total_cases > 0 else 0.0,
    }
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
