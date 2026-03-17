from types import SimpleNamespace

import pytest

from app.services import chat_evaluator_service
from app.services.chat_evaluator_service import (
    ChatEvaluatorError,
    JudgeScoreResult,
)


class FakeJudgeScorer:
    def __init__(self, *, score: float, reasoning: str) -> None:
        self.score = score
        self.reasoning = reasoning

    def score_retrieval_chat(
        self,
        *,
        question: str,
        expected_json: dict[str, object],
        output_json: dict[str, object],
    ) -> JudgeScoreResult:
        assert question
        assert isinstance(expected_json, dict)
        assert isinstance(output_json, dict)
        return JudgeScoreResult(score=self.score, reasoning=self.reasoning)


class FailingJudgeScorer:
    def score_retrieval_chat(
        self,
        *,
        question: str,
        expected_json: dict[str, object],
        output_json: dict[str, object],
    ) -> JudgeScoreResult:
        raise ChatEvaluatorError("Judge unavailable")


def test_evaluate_retrieval_chat_output_scores_grounded_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        chat_evaluator_service,
        "get_judge_scorer",
        lambda: FakeJudgeScorer(score=0.8, reasoning="Grounded and correct."),
    )

    evaluation = chat_evaluator_service.evaluate_retrieval_chat_output(
        question="Who owns Apollo?",
        expected_json={
            "answer_contains": ["Alice"],
            "document_title": "demo.txt",
        },
        output_json={
            "answer": "The owner is Alice.",
            "sources": [
                {
                    "document_id": "doc-1",
                    "chunk_id": "chunk-1",
                    "document_title": "demo.txt",
                    "chunk_index": 0,
                    "snippet": "The owner is Alice.",
                },
            ],
        },
    )

    assert evaluation.rule_score == 1.0
    assert evaluation.judge_score == 0.8
    assert evaluation.score == 0.9
    assert evaluation.passed is True
    assert evaluation.details_json["judge_evaluation"]["reasoning"] == "Grounded and correct."


def test_evaluate_retrieval_chat_output_reflects_missing_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        chat_evaluator_service,
        "get_judge_scorer",
        lambda: FakeJudgeScorer(score=0.9, reasoning="Answer is plausible but uncited."),
    )

    evaluation = chat_evaluator_service.evaluate_retrieval_chat_output(
        question="Who owns Apollo?",
        expected_json={"answer_contains": ["Alice"]},
        output_json={
            "answer": "The owner is Alice.",
            "sources": [],
        },
    )

    checks = evaluation.details_json["rule_evaluation"]["checks"]
    assert checks["answer_present"]["passed"] is True
    assert checks["source_present"]["passed"] is False
    assert evaluation.rule_score == pytest.approx(2 / 3, abs=1e-4)
    assert evaluation.passed is False


def test_evaluate_retrieval_chat_output_captures_judge_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        chat_evaluator_service,
        "get_judge_scorer",
        lambda: FailingJudgeScorer(),
    )

    evaluation = chat_evaluator_service.evaluate_retrieval_chat_output(
        question="Who owns Apollo?",
        expected_json={"answer_contains": ["Alice"]},
        output_json={
            "answer": "The owner is Alice.",
            "sources": [
                {
                    "document_id": "doc-1",
                    "chunk_id": "chunk-1",
                    "document_title": "demo.txt",
                    "chunk_index": 0,
                    "snippet": "The owner is Alice.",
                },
            ],
        },
    )

    assert evaluation.rule_score == 1.0
    assert evaluation.judge_score is None
    assert evaluation.judge_error == "Judge unavailable"
    assert evaluation.score == 1.0
    assert evaluation.passed is True


def test_get_judge_scorer_uses_openai_api_key_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        chat_evaluator_service,
        "get_settings",
        lambda: SimpleNamespace(
            eval_provider="openai",
            eval_api_key="replace_me",
            openai_api_key="openai-test-key",
            eval_model="gpt-4o-mini",
            eval_base_url="https://api.openai.com/v1",
        ),
    )

    scorer = chat_evaluator_service.get_judge_scorer()

    assert isinstance(scorer, chat_evaluator_service.OpenAICompatibleJudgeScorer)
    assert scorer.api_key == "openai-test-key"
    assert scorer.provider_name == "openai"

