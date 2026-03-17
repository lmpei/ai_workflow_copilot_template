from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Callable

from app.services.retrieval_service import ChatProcessingError, GeneratedAnswer, RetrievedChunk
from app.services.scenario_eval_service import (
    ScenarioEvalConfigError,
    resolve_scenario_eval_prompt,
)


class EvalExecutionError(Exception):
    pass


@dataclass(slots=True)
class EvalCaseExecutionResult:
    output_json: dict[str, object]
    metrics_json: dict[str, object]


def serialize_retrieved_chunks(chunks: list[RetrievedChunk]) -> list[dict[str, object]]:
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


def execute_retrieval_chat_case(
    *,
    workspace_id: str,
    eval_run_id: str,
    eval_case_id: str,
    case_index: int,
    question: str,
    retriever,
    answer_generator,
    fallback_answer: str,
    record_trace: Callable[..., str],
) -> EvalCaseExecutionResult:
    started_at = datetime.now(UTC)
    retrieved_chunks: list[RetrievedChunk] = []
    prompt = ""
    answer = ""
    token_input = 0
    token_output = 0
    estimated_cost = 0.0

    try:
        retrieved_chunks = retriever.retrieve(workspace_id=workspace_id, question=question)
        serialized_sources = serialize_retrieved_chunks(retrieved_chunks)

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
            answer = fallback_answer

        latency_ms = max(int((datetime.now(UTC) - started_at).total_seconds() * 1000), 0)
        trace_id = record_trace(
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
        serialized_sources = serialize_retrieved_chunks(retrieved_chunks)
        record_trace(
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
        serialized_sources = serialize_retrieved_chunks(retrieved_chunks)
        record_trace(
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


def execute_eval_case(
    *,
    eval_run_id: str,
    workspace_id: str,
    eval_type: str,
    eval_case_id: str,
    case_index: int,
    question: str,
    retriever,
    answer_generator,
    fallback_answer: str,
    record_trace: Callable[..., str],
) -> EvalCaseExecutionResult:
    if eval_type != "retrieval_chat":
        raise EvalExecutionError(f"Unsupported eval type: {eval_type}")

    return execute_retrieval_chat_case(
        workspace_id=workspace_id,
        eval_run_id=eval_run_id,
        eval_case_id=eval_case_id,
        case_index=case_index,
        question=question,
        retriever=retriever,
        answer_generator=answer_generator,
        fallback_answer=fallback_answer,
        record_trace=record_trace,
    )


def resolve_eval_case_question(
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


def resolve_pass_threshold(scenario_config: dict[str, object]) -> float:
    pass_threshold = scenario_config.get("pass_threshold")
    if not isinstance(pass_threshold, int | float):
        raise EvalExecutionError("Scenario eval config must include a numeric pass_threshold")
    return float(pass_threshold)
