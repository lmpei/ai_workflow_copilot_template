import json
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from app.core.config import get_settings

DEFAULT_PASS_THRESHOLD = 0.7


class ChatEvaluatorError(Exception):
    pass


@dataclass(slots=True)


class JudgeScoreResult:
    score: float | None
    reasoning: str | None = None
    error: str | None = None


@dataclass(slots=True)


class ChatEvaluationResult:
    score: float
    passed: bool
    rule_score: float
    judge_score: float | None
    judge_error: str | None
    details_json: dict[str, object]


class JudgeScorer(Protocol):
    def score_retrieval_chat(
        self,
        *,
        question: str,
        expected_json: dict[str, object],
        output_json: dict[str, object],
    ) -> JudgeScoreResult: ...


@dataclass(slots=True)


class OpenAICompatibleJudgeScorer:
    api_key: str
    model: str
    base_url: str
    provider_name: str

    def score_retrieval_chat(
        self,
        *,
        question: str,
        expected_json: dict[str, object],
        output_json: dict[str, object],
    ) -> JudgeScoreResult:
        if not self.api_key or self.api_key == "replace_me":
            raise ChatEvaluatorError(
                f"{self.provider_name} eval API key must be configured for eval judging",
            )

        prompt = _build_judge_prompt(
            question=question,
            expected_json=expected_json,
            output_json=output_json,
        )
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "temperature": 0.0,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are an evaluator for retrieval-backed chat quality. "
                                "Return strict JSON with keys score and reasoning."
                            ),
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                },
                timeout=30.0,
            )
            response.raise_for_status()
            payload = response.json()
            content = _extract_chat_completion_text(payload)
            parsed = json.loads(content)
        except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise ChatEvaluatorError("Failed to score retrieval chat output") from error

        raw_score = parsed.get("score")
        if not isinstance(raw_score, int | float):
            raise ChatEvaluatorError("Judge output did not include a numeric score")

        normalized_score = max(0.0, min(float(raw_score), 1.0))
        reasoning = parsed.get("reasoning")
        return JudgeScoreResult(
            score=normalized_score,
            reasoning=str(reasoning) if reasoning is not None else None,
        )


def get_judge_scorer() -> JudgeScorer:
    settings = get_settings()
    if settings.eval_provider not in {"openai", "qwen"}:
        raise ChatEvaluatorError(f"Unsupported eval provider: {settings.eval_provider}")
    api_key = settings.eval_api_key
    if api_key == "replace_me" and settings.eval_provider == "openai":
        api_key = settings.openai_api_key
    return OpenAICompatibleJudgeScorer(
        api_key=api_key,
        model=settings.eval_model,
        base_url=settings.eval_base_url,
        provider_name=settings.eval_provider,
    )


def evaluate_retrieval_chat_output(
    *,
    question: str,
    expected_json: dict[str, object],
    output_json: dict[str, object],
    pass_threshold: float = DEFAULT_PASS_THRESHOLD,
    scenario_context: dict[str, object] | None = None,
) -> ChatEvaluationResult:
    rule_checks = _evaluate_rule_checks(expected_json=expected_json, output_json=output_json)
    applicable_checks = [check for check in rule_checks.values() if check["applicable"] is True]
    passed_checks = [check for check in applicable_checks if check["passed"] is True]
    rule_score = (
        len(passed_checks) / len(applicable_checks)
        if applicable_checks
        else 0.0
    )

    judge_result: JudgeScoreResult
    try:
        judge_result = get_judge_scorer().score_retrieval_chat(
            question=question,
            expected_json=expected_json,
            output_json=output_json,
        )
    except ChatEvaluatorError as error:
        judge_result = JudgeScoreResult(score=None, error=str(error))

    final_score = (
        (rule_score + judge_result.score) / 2.0
        if judge_result.score is not None
        else rule_score
    )
    passed = (
        final_score >= max(0.0, min(pass_threshold, 1.0))
        and rule_checks["answer_present"]["passed"] is True
        and rule_checks["source_present"]["passed"] is True
    )

    return ChatEvaluationResult(
        score=round(final_score, 4),
        passed=passed,
        rule_score=round(rule_score, 4),
        judge_score=judge_result.score,
        judge_error=judge_result.error,
        details_json={
            "rule_evaluation": {
                "score": round(rule_score, 4),
                "checks": rule_checks,
            },
            "judge_evaluation": {
                "score": judge_result.score,
                "reasoning": judge_result.reasoning,
                "error": judge_result.error,
            },
            "scenario_context": scenario_context or {},
        },
    )


def _evaluate_rule_checks(
    *,
    expected_json: dict[str, object],
    output_json: dict[str, object],
) -> dict[str, dict[str, object]]:
    answer = output_json.get("answer")
    answer_text = answer.strip() if isinstance(answer, str) else ""
    sources = output_json.get("sources")
    source_list = sources if isinstance(sources, list) else []

    checks: dict[str, dict[str, object]] = {
        "answer_present": {
            "applicable": True,
            "passed": bool(answer_text),
        },
        "source_present": {
            "applicable": True,
            "passed": len(source_list) > 0,
        },
    }

    expected_document_id = expected_json.get("document_id")
    expected_document_title = expected_json.get("document_title")
    if isinstance(expected_document_id, str) and expected_document_id:
        checks["expected_document_hit"] = {
            "applicable": True,
            "passed": any(
                isinstance(source, dict) and source.get("document_id") == expected_document_id
                for source in source_list
            ),
        }
    elif isinstance(expected_document_title, str) and expected_document_title:
        checks["expected_document_hit"] = {
            "applicable": True,
            "passed": any(
                isinstance(source, dict) and source.get("document_title") == expected_document_title
                for source in source_list
            ),
        }
    else:
        checks["expected_document_hit"] = {
            "applicable": False,
            "passed": None,
        }

    answer_contains = expected_json.get("answer_contains")
    expected_terms = (
        [str(item).strip().lower() for item in answer_contains if str(item).strip()]
        if isinstance(answer_contains, list)
        else []
    )
    if expected_terms:
        lowered_answer = answer_text.lower()
        checks["answer_contains"] = {
            "applicable": True,
            "passed": all(term in lowered_answer for term in expected_terms),
        }
    else:
        checks["answer_contains"] = {
            "applicable": False,
            "passed": None,
        }

    return checks


def _build_judge_prompt(
    *,
    question: str,
    expected_json: dict[str, object],
    output_json: dict[str, object],
) -> str:
    return (
        "Evaluate the following retrieval-backed chat response.\n"
        "Return JSON only with keys: score, reasoning.\n\n"
        f"Question:\n{question}\n\n"
        f"Expected:\n{json.dumps(expected_json, ensure_ascii=False, sort_keys=True)}\n\n"
        f"Actual:\n{json.dumps(output_json, ensure_ascii=False, sort_keys=True)}\n\n"
        "Score from 0.0 to 1.0 based on answer correctness and grounding in cited sources."
    )


def _extract_chat_completion_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise KeyError("choices")

    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise KeyError("message")

    content = message.get("content")
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = [
            str(item.get("text", ""))
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        return "\n".join(part for part in text_parts if part)

    raise TypeError("Unsupported chat completion content type")
