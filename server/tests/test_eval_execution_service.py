import asyncio
from uuid import uuid4

import pytest

from app.core.database import reset_database_for_tests
from app.repositories import eval_repository, trace_repository
from app.repositories.user_repository import create_user
from app.repositories.workspace_repository import create_workspace
from app.schemas.workspace import WorkspaceCreate
from app.services import chat_evaluator_service, eval_execution_service
from app.services.retrieval_service import ChatProcessingError, GeneratedAnswer, RetrievedChunk
from app.workers.task_worker import run_eval_run


class FakeJob:
    def __init__(self, job_id: str) -> None:
        self.job_id = job_id


class FakePool:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.closed = False

    async def enqueue_job(self, function_name: str, eval_run_id: str, _queue_name: str) -> FakeJob:
        self.calls.append(
            {
                "function_name": function_name,
                "eval_run_id": eval_run_id,
                "queue_name": _queue_name,
            },
        )
        return FakeJob("eval-job-123")

    async def aclose(self) -> None:
        self.closed = True


@pytest.fixture(autouse=True)
def reset_database() -> None:
    reset_database_for_tests()


class FakeRetriever:
    def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
        assert workspace_id
        return [
            RetrievedChunk(
                document_id="doc-1",
                chunk_id=f"chunk-{question[:8]}",
                document_title="demo.txt",
                chunk_index=0,
                snippet=f"Snippet for {question}",
                content=f"Context for {question}",
            ),
        ]


class FakeAnswerGenerator:
    def generate_answer(
        self,
        *,
        question: str,
        retrieved_chunks: list[RetrievedChunk],
    ) -> GeneratedAnswer:
        assert retrieved_chunks
        return GeneratedAnswer(
            answer=f"Answer for {question}",
            prompt=f"Prompt for {question}",
            token_input=11,
            token_output=7,
            estimated_cost=0.0,
        )


class PartiallyFailingAnswerGenerator:
    def generate_answer(
        self,
        *,
        question: str,
        retrieved_chunks: list[RetrievedChunk],
    ) -> GeneratedAnswer:
        assert retrieved_chunks
        if "fail" in question.lower():
            raise ChatProcessingError("Judge unavailable")
        return GeneratedAnswer(
            answer=f"Answer for {question}",
            prompt=f"Prompt for {question}",
            token_input=9,
            token_output=4,
            estimated_cost=0.0,
        )


class ExplodingRetriever:
    def retrieve(self, *, workspace_id: str, question: str) -> list[RetrievedChunk]:
        raise RuntimeError("Vector store unavailable")


class FakeJudgeScorer:
    def score_retrieval_chat(
        self,
        *,
        question: str,
        expected_json: dict[str, object],
        output_json: dict[str, object],
    ) -> chat_evaluator_service.JudgeScoreResult:
        assert question
        assert isinstance(expected_json, dict)
        assert isinstance(output_json, dict)
        return chat_evaluator_service.JudgeScoreResult(
            score=0.8,
            reasoning="Grounded and correct.",
        )


class FailingJudgeScorer:
    def score_retrieval_chat(
        self,
        *,
        question: str,
        expected_json: dict[str, object],
        output_json: dict[str, object],
    ) -> chat_evaluator_service.JudgeScoreResult:
        raise chat_evaluator_service.ChatEvaluatorError("Judge unavailable")



def _create_eval_run_fixture(*, questions: list[str]) -> dict[str, str]:
    unique_suffix = uuid4().hex
    user = create_user(
        email=f"eval-run-{unique_suffix}@example.com",
        password_hash="not-used-in-this-test",
        name="Eval Runner",
    )
    workspace = create_workspace(
        WorkspaceCreate(name="Eval Workspace", type="research"),
        owner_id=user.id,
    )
    dataset = eval_repository.create_eval_dataset(
        workspace_id=workspace.id,
        name="Grounded Chat Eval",
        eval_type="retrieval_chat",
        created_by=user.id,
    )
    for index, question in enumerate(questions):
        eval_repository.create_eval_case(
            dataset_id=dataset.id,
            case_index=index,
            input_json={"question": question},
            expected_json={},
        )
    eval_run = eval_repository.create_eval_run(
        workspace_id=workspace.id,
        dataset_id=dataset.id,
        eval_type=dataset.eval_type,
        created_by=user.id,
        summary_json={
            "total_cases": len(questions),
            "completed_cases": 0,
            "failed_cases": 0,
        },
    )
    return {
        "workspace_id": workspace.id,
        "user_id": user.id,
        "dataset_id": dataset.id,
        "eval_run_id": eval_run.id,
    }



def test_enqueue_eval_run_uses_arq_pool(monkeypatch: pytest.MonkeyPatch) -> None:
    fixture = _create_eval_run_fixture(questions=["Who owns Apollo?"])
    fake_pool = FakePool()

    async def fake_create_pool(_settings: object) -> FakePool:
        return fake_pool

    monkeypatch.setattr(eval_execution_service, "create_pool", fake_create_pool)
    monkeypatch.setattr(eval_execution_service, "build_redis_settings", lambda: object())

    job_id = asyncio.run(eval_execution_service.enqueue_eval_run(fixture["eval_run_id"]))

    assert job_id == "eval-job-123"
    assert fake_pool.calls == [
        {
            "function_name": eval_execution_service.EVAL_EXECUTION_JOB_NAME,
            "eval_run_id": fixture["eval_run_id"],
            "queue_name": "platform_tasks",
        },
    ]
    assert fake_pool.closed is True



def test_run_eval_execution_completes_dataset_and_persists_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _create_eval_run_fixture(
        questions=["Who owns Apollo?", "How many milestones are there?"],
    )
    monkeypatch.setattr(
        eval_execution_service.retrieval_service,
        "get_retriever",
        lambda: FakeRetriever(),
    )
    monkeypatch.setattr(
        eval_execution_service.retrieval_service,
        "get_answer_generator",
        lambda: FakeAnswerGenerator(),
    )
    monkeypatch.setattr(
        chat_evaluator_service,
        "get_judge_scorer",
        lambda: FakeJudgeScorer(),
    )

    summary = eval_execution_service.run_eval_execution(fixture["eval_run_id"])
    persisted_run = eval_repository.get_eval_run(fixture["eval_run_id"])
    persisted_results = eval_repository.list_eval_run_results(fixture["eval_run_id"])
    persisted_traces = trace_repository.list_traces_for_eval_run(fixture["eval_run_id"])

    assert summary == {
        "eval_run_id": fixture["eval_run_id"],
        "status": "completed",
        "total_cases": 2,
        "completed_cases": 2,
        "failed_cases": 0,
    }
    assert persisted_run is not None
    assert persisted_run.status == "completed"
    assert persisted_run.summary_json == {
        "total_cases": 2,
        "completed_cases": 2,
        "failed_cases": 0,
    }
    assert len(persisted_results) == 2
    assert all(result.status == "completed" for result in persisted_results)
    assert all("answer" in result.output_json for result in persisted_results)
    assert all("evaluation" in result.output_json for result in persisted_results)
    assert all(result.metrics_json["retrieval_hit"] is True for result in persisted_results)
    assert all(result.metrics_json["rule_score"] == 1.0 for result in persisted_results)
    assert all(result.metrics_json["judge_score"] == 0.8 for result in persisted_results)
    assert all(result.score == 0.9 for result in persisted_results)
    assert all(result.passed is True for result in persisted_results)
    assert len(persisted_traces) == 2
    assert all(trace.trace_type == "eval" for trace in persisted_traces)



def test_run_eval_execution_marks_run_failed_and_preserves_partial_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _create_eval_run_fixture(
        questions=["Who owns Apollo?", "Please fail this case"],
    )
    monkeypatch.setattr(
        eval_execution_service.retrieval_service,
        "get_retriever",
        lambda: FakeRetriever(),
    )
    monkeypatch.setattr(
        eval_execution_service.retrieval_service,
        "get_answer_generator",
        lambda: PartiallyFailingAnswerGenerator(),
    )
    monkeypatch.setattr(
        chat_evaluator_service,
        "get_judge_scorer",
        lambda: FakeJudgeScorer(),
    )

    summary = eval_execution_service.run_eval_execution(fixture["eval_run_id"])
    persisted_run = eval_repository.get_eval_run(fixture["eval_run_id"])
    persisted_results = eval_repository.list_eval_run_results(fixture["eval_run_id"])
    persisted_traces = trace_repository.list_traces_for_eval_run(fixture["eval_run_id"])

    assert summary == {
        "eval_run_id": fixture["eval_run_id"],
        "status": "failed",
        "total_cases": 2,
        "completed_cases": 1,
        "failed_cases": 1,
    }
    assert persisted_run is not None
    assert persisted_run.status == "failed"
    assert persisted_run.summary_json == {
        "total_cases": 2,
        "completed_cases": 1,
        "failed_cases": 1,
    }
    assert persisted_run.error_message == "Judge unavailable"
    assert len(persisted_results) == 2
    assert [result.status for result in persisted_results] == ["completed", "failed"]
    assert persisted_results[0].score == 0.9
    assert persisted_results[0].passed is True
    assert persisted_results[1].error_message == "Judge unavailable"
    assert len(persisted_traces) == 2



def test_run_eval_execution_captures_judge_failure_without_losing_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _create_eval_run_fixture(questions=["Who owns Apollo?"])
    monkeypatch.setattr(
        eval_execution_service.retrieval_service,
        "get_retriever",
        lambda: FakeRetriever(),
    )
    monkeypatch.setattr(
        eval_execution_service.retrieval_service,
        "get_answer_generator",
        lambda: FakeAnswerGenerator(),
    )
    monkeypatch.setattr(
        chat_evaluator_service,
        "get_judge_scorer",
        lambda: FailingJudgeScorer(),
    )

    summary = eval_execution_service.run_eval_execution(fixture["eval_run_id"])
    persisted_result = eval_repository.list_eval_run_results(fixture["eval_run_id"])[0]

    assert summary["status"] == "completed"
    assert persisted_result.status == "completed"
    assert persisted_result.score == 1.0
    assert persisted_result.passed is True
    assert persisted_result.metrics_json["judge_error"] == "Judge unavailable"



def test_run_eval_execution_marks_run_failed_on_worker_level_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _create_eval_run_fixture(questions=["Who owns Apollo?"])
    monkeypatch.setattr(
        eval_execution_service.retrieval_service,
        "get_retriever",
        lambda: ExplodingRetriever(),
    )
    monkeypatch.setattr(
        chat_evaluator_service,
        "get_judge_scorer",
        lambda: FailingJudgeScorer(),
    )

    summary = eval_execution_service.run_eval_execution(fixture["eval_run_id"])
    persisted_run = eval_repository.get_eval_run(fixture["eval_run_id"])
    persisted_results = eval_repository.list_eval_run_results(fixture["eval_run_id"])

    assert summary["status"] == "failed"
    assert persisted_run is not None
    assert persisted_run.status == "failed"
    assert persisted_run.error_message == "Vector store unavailable"
    assert len(persisted_results) == 1
    assert persisted_results[0].status == "failed"
    assert persisted_results[0].error_message == "Vector store unavailable"



def test_run_eval_run_worker_entrypoint_executes_eval_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _create_eval_run_fixture(questions=["Who owns Apollo?"])
    monkeypatch.setattr(
        eval_execution_service.retrieval_service,
        "get_retriever",
        lambda: FakeRetriever(),
    )
    monkeypatch.setattr(
        eval_execution_service.retrieval_service,
        "get_answer_generator",
        lambda: FakeAnswerGenerator(),
    )
    monkeypatch.setattr(
        chat_evaluator_service,
        "get_judge_scorer",
        lambda: FakeJudgeScorer(),
    )

    output = asyncio.run(run_eval_run({}, fixture["eval_run_id"]))
    persisted_run = eval_repository.get_eval_run(fixture["eval_run_id"])

    assert output["eval_run_id"] == fixture["eval_run_id"]
    assert output["status"] == "completed"
    assert persisted_run is not None
    assert persisted_run.status == "completed"
