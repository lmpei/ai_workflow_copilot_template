import json
from dataclasses import dataclass
from typing import Protocol

from app.core.config import get_settings
from app.services.model_interface_service import (
    ModelInterfaceError,
    ModelMessage,
    OpenAICompatibleModelInterface,
    OpenAICompatibleModelSettings,
    resolve_api_key,
)

DEFAULT_PASS_THRESHOLD = 0.7
RESEARCH_ANALYSIS_RUN_REGRESSION_BASELINE_VERSION = "stage_j_mcp_learning_closeout_v1"


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
            response = OpenAICompatibleModelInterface(
                settings=OpenAICompatibleModelSettings(
                    api_key=self.api_key,
                    model=self.model,
                    base_url=self.base_url,
                    provider_name=self.provider_name,
                )
            ).generate_json_object(
                temperature=0.0,
                messages=[
                    ModelMessage(
                        role="system",
                        content=(
                            "You are an evaluator for retrieval-backed chat quality. "
                            "Return strict JSON with keys score and reasoning."
                        ),
                    ),
                    ModelMessage(role="user", content=prompt),
                ],
            )
        except ModelInterfaceError as error:
            raise ChatEvaluatorError("Failed to score retrieval chat output") from error

        raw_score = response.data.get("score")
        if not isinstance(raw_score, int | float):
            raise ChatEvaluatorError("Judge output did not include a numeric score")

        normalized_score = max(0.0, min(float(raw_score), 1.0))
        reasoning = response.data.get("reasoning")
        return JudgeScoreResult(
            score=normalized_score,
            reasoning=str(reasoning) if reasoning is not None else None,
        )


def get_judge_scorer() -> JudgeScorer:
    settings = get_settings()
    if settings.eval_provider not in {"openai", "qwen"}:
        raise ChatEvaluatorError(f"Unsupported eval provider: {settings.eval_provider}")
    api_key = resolve_api_key(
        provider_name=settings.eval_provider,
        configured_api_key=settings.eval_api_key,
        openai_api_key=settings.openai_api_key,
    )
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
    rule_score = len(passed_checks) / len(applicable_checks) if applicable_checks else 0.0

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


def evaluate_research_tool_assisted_output(
    *,
    question: str,
    expected_json: dict[str, object],
    output_json: dict[str, object],
    trace_metadata: dict[str, object] | None = None,
    pass_threshold: float = DEFAULT_PASS_THRESHOLD,
) -> ChatEvaluationResult:
    rule_checks = _evaluate_tool_assisted_rule_checks(
        expected_json=expected_json,
        output_json=output_json,
        trace_metadata=trace_metadata or {},
    )
    applicable_checks = [check for check in rule_checks.values() if check["applicable"] is True]
    passed_checks = [check for check in applicable_checks if check["passed"] is True]
    rule_score = len(passed_checks) / len(applicable_checks) if applicable_checks else 0.0

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
        and rule_checks["tool_steps_present"]["passed"] is True
        and (
            rule_checks["source_present"]["passed"] is True
            or rule_checks["honest_degraded_path"]["passed"] is True
        )
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
            "scenario_context": {
                "mode": "research_tool_assisted",
                **(trace_metadata or {}),
            },
        },
    )


def evaluate_research_analysis_run_regression(
    *,
    run_json: dict[str, object],
    trace_response_json: dict[str, object] | None = None,
    trace_metadata: dict[str, object] | None = None,
    trace_type: str | None = None,
) -> dict[str, object]:
    response_json = trace_response_json or {}
    metadata_json = trace_metadata or {}

    def _read_string(*values: object) -> str | None:
        for value in values:
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    def _read_int(*values: object) -> int | None:
        for value in values:
            if isinstance(value, bool):
                continue
            if isinstance(value, int):
                return value
        return None

    def _read_bool(*values: object) -> bool | None:
        for value in values:
            if isinstance(value, bool):
                return value
        return None

    status = run_json.get("status")
    mode = _read_string(run_json.get("mode"))
    answer = run_json.get("answer")
    answer_text = answer.strip() if isinstance(answer, str) else ""
    trace_id = run_json.get("trace_id")
    resumed_from_run_id = run_json.get("resumed_from_run_id")

    raw_sources = run_json.get("sources")
    sources = raw_sources if isinstance(raw_sources, list) else []
    raw_tool_steps = run_json.get("tool_steps")
    tool_steps = raw_tool_steps if isinstance(raw_tool_steps, list) else []
    run_memory = run_json.get("run_memory")
    run_memory_json = run_memory if isinstance(run_memory, dict) else {}

    degraded_reason = _read_string(
        run_json.get("degraded_reason"),
        response_json.get("degraded_reason"),
        metadata_json.get("degraded_reason"),
    )
    prompt_present = isinstance(metadata_json.get("prompt"), str) and bool(str(metadata_json.get("prompt")).strip())

    has_sources = len(sources) > 0
    has_external_sources = any(
        isinstance(source, dict) and source.get("source_kind") == "external_context"
        for source in sources
    )
    has_tool_steps = len(tool_steps) > 0
    has_run_memory = (
        bool(run_memory_json)
        and isinstance(run_memory_json.get("summary"), str)
        and bool(str(run_memory_json.get("summary")).strip())
    )
    resumed_visible = (
        isinstance(resumed_from_run_id, str)
        and bool(resumed_from_run_id)
        and (
            response_json.get("resumed_from_run_id") == resumed_from_run_id
            or metadata_json.get("resumed_from_run_id") == resumed_from_run_id
        )
        and any(
            isinstance(step, dict) and step.get("tool_name") == "resume_run_memory"
            for step in tool_steps
        )
    )

    connector_id = _read_string(
        run_json.get("connector_id"),
        response_json.get("connector_id"),
        metadata_json.get("connector_id"),
    )
    connector_consent_state = _read_string(
        run_json.get("connector_consent_state"),
        response_json.get("connector_consent_state"),
        metadata_json.get("connector_consent_state"),
    )
    external_context_used = _read_bool(
        run_json.get("external_context_used"),
        response_json.get("external_context_used"),
        metadata_json.get("external_context_used"),
    )
    external_match_count = _read_int(
        run_json.get("external_match_count"),
        response_json.get("external_match_count"),
        metadata_json.get("external_match_count"),
    )
    selected_external_resource_snapshot_id = _read_string(
        run_json.get("selected_external_resource_snapshot_id"),
        response_json.get("selected_external_resource_snapshot_id"),
        metadata_json.get("selected_external_resource_snapshot_id"),
    )
    external_resource_snapshot_id = _read_string(
        run_json.get("external_resource_snapshot_id"),
        response_json.get("external_resource_snapshot_id"),
        metadata_json.get("external_resource_snapshot_id"),
    )
    context_selection_mode = _read_string(
        run_json.get("context_selection_mode"),
        response_json.get("context_selection_mode"),
        metadata_json.get("context_selection_mode"),
    )
    mcp_server_id = _read_string(
        run_json.get("mcp_server_id"),
        response_json.get("mcp_server_id"),
        metadata_json.get("mcp_server_id"),
    )
    mcp_resource_id = _read_string(
        run_json.get("mcp_resource_id"),
        response_json.get("mcp_resource_id"),
        metadata_json.get("mcp_resource_id"),
    )
    mcp_resource_uri = _read_string(
        run_json.get("mcp_resource_uri"),
        response_json.get("mcp_resource_uri"),
        metadata_json.get("mcp_resource_uri"),
    )
    mcp_resource_display_name = _read_string(
        run_json.get("mcp_resource_display_name"),
        response_json.get("mcp_resource_display_name"),
        metadata_json.get("mcp_resource_display_name"),
    )
    mcp_tool_name = _read_string(
        run_json.get("mcp_tool_name"),
        response_json.get("mcp_tool_name"),
        metadata_json.get("mcp_tool_name"),
    )
    mcp_prompt_name = _read_string(
        run_json.get("mcp_prompt_name"),
        response_json.get("mcp_prompt_name"),
        metadata_json.get("mcp_prompt_name"),
    )
    mcp_transport = _read_string(
        run_json.get("mcp_transport"),
        response_json.get("mcp_transport"),
        metadata_json.get("mcp_transport"),
    )
    mcp_endpoint_source = _read_string(
        run_json.get("mcp_endpoint_source"),
        response_json.get("mcp_endpoint_source"),
        metadata_json.get("mcp_endpoint_source"),
    )
    mcp_endpoint_display_name = _read_string(
        run_json.get("mcp_endpoint_display_name"),
        response_json.get("mcp_endpoint_display_name"),
        metadata_json.get("mcp_endpoint_display_name"),
    )
    mcp_endpoint_auth_state = _read_string(
        run_json.get("mcp_endpoint_auth_state"),
        response_json.get("mcp_endpoint_auth_state"),
        metadata_json.get("mcp_endpoint_auth_state"),
    )
    mcp_endpoint_auth_detail = _read_string(
        run_json.get("mcp_endpoint_auth_detail"),
        response_json.get("mcp_endpoint_auth_detail"),
        metadata_json.get("mcp_endpoint_auth_detail"),
    )
    mcp_read_status = _read_string(
        run_json.get("mcp_read_status"),
        response_json.get("mcp_read_status"),
        metadata_json.get("mcp_read_status"),
    )
    mcp_transport_error = _read_string(
        run_json.get("mcp_transport_error"),
        response_json.get("mcp_transport_error"),
        metadata_json.get("mcp_transport_error"),
    )
    resource_selection_mode = (
        "explicit"
        if selected_external_resource_snapshot_id
        else "auto"
        if external_resource_snapshot_id
        else "none"
    )

    is_external_context_run = (
        mode == "research_external_context"
        or trace_type == "research_external_context_run"
        or connector_id == "research_external_context"
    )
    is_mcp_resource_path = is_external_context_run and context_selection_mode == "mcp_resource"

    checks = {
        "terminal_status_valid": status in {"completed", "degraded", "failed"},
        "trace_link_present": isinstance(trace_id, str) and bool(trace_id.strip()),
        "trace_type_valid": trace_type in {"research_tool_assisted_run", "research_external_context_run"},
        "prompt_present": prompt_present,
        "answer_present_when_not_failed": (status == "failed") or bool(answer_text),
        "tool_steps_visible_when_not_failed": (status == "failed") or has_tool_steps,
        "run_memory_present_when_not_failed": (status == "failed") or has_run_memory,
        "grounded_or_honest_degraded_when_not_failed": (status == "failed")
        or has_sources
        or bool(degraded_reason),
        "resumed_memory_visible_when_applicable": (
            not isinstance(resumed_from_run_id, str) or not resumed_from_run_id
        )
        or resumed_visible,
        "connector_id_visible_when_applicable": (not is_external_context_run)
        or connector_id == "research_external_context",
        "connector_consent_state_visible_when_applicable": (not is_external_context_run)
        or connector_consent_state in {"granted", "not_granted", "revoked"},
        "external_context_usage_visible_when_applicable": (not is_external_context_run)
        or isinstance(external_context_used, bool),
        "external_match_count_visible_when_applicable": (not is_external_context_run)
        or (isinstance(external_match_count, int) and external_match_count >= 0),
        "selected_resource_snapshot_visibility_when_applicable": (not is_external_context_run)
        or resource_selection_mode != "explicit"
        or bool(selected_external_resource_snapshot_id),
        "resource_snapshot_visibility_when_applicable": (not is_external_context_run)
        or external_context_used is not True
        or bool(external_resource_snapshot_id),
        "external_context_visibility_consistent_when_applicable": (not is_external_context_run)
        or (
            isinstance(external_context_used, bool)
            and isinstance(external_match_count, int)
            and (
                (external_context_used is True and has_external_sources and external_match_count > 0)
                or (external_context_used is False and not has_external_sources and external_match_count == 0)
            )
        ),
        "resource_selection_consistent_when_applicable": (not is_external_context_run)
        or (
            (resource_selection_mode == "explicit" and external_context_used is True and external_resource_snapshot_id == selected_external_resource_snapshot_id)
            or (resource_selection_mode == "explicit" and external_context_used is False and external_resource_snapshot_id is None)
            or (resource_selection_mode == "auto" and external_context_used is True and bool(external_resource_snapshot_id))
            or (resource_selection_mode == "none" and external_context_used is False and external_resource_snapshot_id is None)
            or (resource_selection_mode == "none" and external_context_used is True and bool(external_resource_snapshot_id))
        ),
        "mcp_server_visibility_when_applicable": (not is_mcp_resource_path) or bool(mcp_server_id),
        "mcp_endpoint_visibility_when_applicable": (not is_external_context_run)
        or (
            bool(mcp_endpoint_source)
            and bool(mcp_endpoint_display_name)
        ),
        "mcp_auth_state_visibility_when_applicable": (not is_external_context_run)
        or mcp_endpoint_auth_state in {"not_required", "configured", "missing", "denied"},
        "mcp_auth_detail_visibility_when_applicable": (not is_external_context_run)
        or mcp_endpoint_auth_state not in {"missing", "denied"}
        or bool(mcp_endpoint_auth_detail),
        "mcp_resource_visibility_when_applicable": (not is_mcp_resource_path)
        or (
            bool(mcp_resource_id)
            and bool(mcp_resource_uri)
            and bool(mcp_resource_display_name)
        ),
        "mcp_tool_visibility_when_applicable": (not is_mcp_resource_path) or bool(mcp_tool_name),
        "mcp_prompt_visibility_when_applicable": (not is_mcp_resource_path) or bool(mcp_prompt_name),
        "mcp_transport_visibility_when_applicable": (not is_external_context_run)
        or mcp_transport in {"stdio_process", "local_inproc"},
        "mcp_read_status_visibility_when_applicable": (not is_external_context_run)
        or mcp_read_status
        in {
            "consent_required",
            "consent_revoked",
            "auth_required",
            "auth_denied",
            "snapshot_reused",
            "used",
            "transport_unavailable",
            "no_useful_matches",
        },
        "mcp_transport_error_visibility_when_applicable": (not is_mcp_resource_path)
        or mcp_read_status != "transport_unavailable"
        or bool(mcp_transport_error),
        "remote_mcp_outcome_consistent_when_applicable": (not is_external_context_run)
        or (
            connector_consent_state == "not_granted"
            and mcp_read_status == "consent_required"
            and external_context_used is False
            and external_match_count == 0
        )
        or (
            connector_consent_state == "revoked"
            and mcp_read_status == "consent_revoked"
            and external_context_used is False
            and external_match_count == 0
        )
        or (
            context_selection_mode == "mcp_resource"
            and degraded_reason == "external_context_auth_required"
            and mcp_read_status == "auth_required"
            and mcp_endpoint_auth_state == "missing"
            and external_context_used is False
        )
        or (
            context_selection_mode == "mcp_resource"
            and degraded_reason == "external_context_auth_denied"
            and mcp_read_status == "auth_denied"
            and mcp_endpoint_auth_state == "denied"
            and external_context_used is False
        )
        or (
            context_selection_mode == "snapshot"
            and mcp_read_status == "snapshot_reused"
        )
        or (
            context_selection_mode == "mcp_resource"
            and degraded_reason == "external_context_unavailable"
            and mcp_read_status == "transport_unavailable"
            and external_context_used is False
        )
        or (
            context_selection_mode == "mcp_resource"
            and degraded_reason == "external_context_no_useful_matches"
            and mcp_read_status == "no_useful_matches"
            and external_context_used is False
        )
        or (
            context_selection_mode == "mcp_resource"
            and external_context_used is True
            and mcp_read_status == "used"
            and isinstance(external_match_count, int)
            and external_match_count > 0
        ),
        "consent_lifecycle_consistent_when_applicable": (not is_external_context_run)
        or connector_consent_state == "granted"
        or (
            connector_consent_state == "not_granted"
            and external_context_used is False
            and external_match_count == 0
            and not has_external_sources
            and degraded_reason == "connector_consent_required"
            and external_resource_snapshot_id is None
        )
        or (
            connector_consent_state == "revoked"
            and external_context_used is False
            and external_match_count == 0
            and not has_external_sources
            and degraded_reason == "connector_consent_revoked"
            and external_resource_snapshot_id is None
        ),
    }

    issues: list[str] = []
    if status == "failed":
        issues.append("run_failed")
    if checks["trace_link_present"] is False:
        issues.append("missing_trace_link")
    if checks["trace_type_valid"] is False:
        issues.append("invalid_trace_type")
    if checks["prompt_present"] is False:
        issues.append("missing_prompt")
    if checks["answer_present_when_not_failed"] is False:
        issues.append("missing_answer")
    if checks["tool_steps_visible_when_not_failed"] is False:
        issues.append("missing_tool_steps")
    if checks["run_memory_present_when_not_failed"] is False:
        issues.append("missing_run_memory")
    if checks["grounded_or_honest_degraded_when_not_failed"] is False:
        issues.append("missing_grounding_or_honest_degraded_reason")
    if checks["resumed_memory_visible_when_applicable"] is False:
        issues.append("missing_resumed_memory_visibility")
    if checks["connector_id_visible_when_applicable"] is False:
        issues.append("missing_connector_id_visibility")
    if checks["connector_consent_state_visible_when_applicable"] is False:
        issues.append("missing_connector_consent_state_visibility")
    if checks["external_context_usage_visible_when_applicable"] is False:
        issues.append("missing_external_context_usage_visibility")
    if checks["external_match_count_visible_when_applicable"] is False:
        issues.append("missing_external_match_count_visibility")
    if checks["selected_resource_snapshot_visibility_when_applicable"] is False:
        issues.append("missing_selected_resource_snapshot_visibility")
    if checks["resource_snapshot_visibility_when_applicable"] is False:
        issues.append("missing_resource_snapshot_visibility")
    if checks["external_context_visibility_consistent_when_applicable"] is False:
        issues.append("inconsistent_external_context_visibility")
    if checks["resource_selection_consistent_when_applicable"] is False:
        issues.append("inconsistent_resource_selection_visibility")
    if checks["mcp_server_visibility_when_applicable"] is False:
        issues.append("missing_mcp_server_visibility")
    if checks["mcp_endpoint_visibility_when_applicable"] is False:
        issues.append("missing_mcp_endpoint_visibility")
    if checks["mcp_auth_state_visibility_when_applicable"] is False:
        issues.append("missing_mcp_auth_state_visibility")
    if checks["mcp_auth_detail_visibility_when_applicable"] is False:
        issues.append("missing_mcp_auth_detail_visibility")
    if checks["mcp_resource_visibility_when_applicable"] is False:
        issues.append("missing_mcp_resource_visibility")
    if checks["mcp_tool_visibility_when_applicable"] is False:
        issues.append("missing_mcp_tool_visibility")
    if checks["mcp_prompt_visibility_when_applicable"] is False:
        issues.append("missing_mcp_prompt_visibility")
    if checks["mcp_transport_visibility_when_applicable"] is False:
        issues.append("missing_mcp_transport_visibility")
    if checks["mcp_read_status_visibility_when_applicable"] is False:
        issues.append("missing_remote_mcp_read_status_visibility")
    if checks["mcp_transport_error_visibility_when_applicable"] is False:
        issues.append("missing_mcp_transport_error_visibility")
    if checks["remote_mcp_outcome_consistent_when_applicable"] is False:
        issues.append("inconsistent_remote_mcp_outcome_visibility")
    if checks["consent_lifecycle_consistent_when_applicable"] is False:
        issues.append("inconsistent_connector_consent_lifecycle")

    passed = all(checks.values()) and not issues

    return {
        "baseline_version": RESEARCH_ANALYSIS_RUN_REGRESSION_BASELINE_VERSION,
        "passed": passed,
        "checks": checks,
        "issues": issues,
        "signals": {
            "status": status,
            "mode": mode,
            "has_sources": has_sources,
            "has_external_sources": has_external_sources,
            "degraded_reason": degraded_reason,
            "resumed_from_run_id": resumed_from_run_id,
            "trace_type": trace_type,
            "used_run_memory": isinstance(resumed_from_run_id, str) and bool(resumed_from_run_id),
            "connector_id": connector_id,
            "connector_consent_state": connector_consent_state,
            "external_context_used": external_context_used,
            "external_match_count": external_match_count,
            "selected_external_resource_snapshot_id": selected_external_resource_snapshot_id,
            "external_resource_snapshot_id": external_resource_snapshot_id,
            "resource_selection_mode": resource_selection_mode,
            "context_selection_mode": context_selection_mode,
            "mcp_server_id": mcp_server_id,
            "mcp_endpoint_source": mcp_endpoint_source,
            "mcp_endpoint_display_name": mcp_endpoint_display_name,
            "mcp_endpoint_auth_state": mcp_endpoint_auth_state,
            "mcp_endpoint_auth_detail": mcp_endpoint_auth_detail,
            "mcp_resource_id": mcp_resource_id,
            "mcp_resource_uri": mcp_resource_uri,
            "mcp_resource_display_name": mcp_resource_display_name,
            "mcp_tool_name": mcp_tool_name,
            "mcp_prompt_name": mcp_prompt_name,
            "mcp_transport": mcp_transport,
            "mcp_read_status": mcp_read_status,
            "mcp_transport_error": mcp_transport_error,
        },
    }


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


def _evaluate_tool_assisted_rule_checks(
    *,
    expected_json: dict[str, object],
    output_json: dict[str, object],
    trace_metadata: dict[str, object],
) -> dict[str, dict[str, object]]:
    checks = _evaluate_rule_checks(expected_json=expected_json, output_json=output_json)

    raw_tool_steps = output_json.get("tool_steps")
    tool_steps = raw_tool_steps if isinstance(raw_tool_steps, list) else []
    degraded_reason = output_json.get("degraded_reason")
    if not isinstance(degraded_reason, str) or not degraded_reason:
        degraded_reason = trace_metadata.get("degraded_reason")
    normalized_degraded_reason = degraded_reason if isinstance(degraded_reason, str) and degraded_reason else None

    checks["tool_steps_present"] = {
        "applicable": True,
        "passed": len(tool_steps) > 0,
    }

    has_sources = checks["source_present"]["passed"] is True
    allow_honest_degraded = bool(expected_json.get("allow_degraded_without_sources"))
    checks["honest_degraded_path"] = {
        "applicable": not has_sources,
        "passed": bool(normalized_degraded_reason) if allow_honest_degraded else False,
    }
    checks["degraded_reason_visible"] = {
        "applicable": not has_sources,
        "passed": bool(normalized_degraded_reason),
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
