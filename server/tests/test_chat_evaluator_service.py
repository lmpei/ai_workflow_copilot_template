from types import SimpleNamespace

import pytest

from app.services import chat_evaluator_service
from app.services.chat_evaluator_service import (
    ChatEvaluatorError,
    JudgeScoreResult,
    RESEARCH_ANALYSIS_RUN_REGRESSION_BASELINE_VERSION,
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


def test_evaluate_research_tool_assisted_output_accepts_visible_tool_steps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        chat_evaluator_service,
        "get_judge_scorer",
        lambda: FakeJudgeScorer(score=0.8, reasoning="Grounded and transparent."),
    )

    evaluation = chat_evaluator_service.evaluate_research_tool_assisted_output(
        question="What should we conclude from the current research material?",
        expected_json={},
        output_json={
            "answer": "The strongest current signal is the pricing shift.",
            "sources": [
                {
                    "document_id": "doc-1",
                    "chunk_id": "chunk-1",
                    "document_title": "market-notes.txt",
                    "chunk_index": 0,
                    "snippet": "The strongest current signal is the pricing shift.",
                },
            ],
            "tool_steps": [
                {"tool_name": "list_workspace_documents", "summary": "Checked the material."},
                {"tool_name": "search_documents", "summary": "Found the strongest evidence."},
            ],
        },
    )

    checks = evaluation.details_json["rule_evaluation"]["checks"]
    assert checks["tool_steps_present"]["passed"] is True
    assert checks["source_present"]["passed"] is True
    assert checks["honest_degraded_path"]["applicable"] is False
    assert evaluation.passed is True


def test_evaluate_research_tool_assisted_output_accepts_honest_degraded_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        chat_evaluator_service,
        "get_judge_scorer",
        lambda: FakeJudgeScorer(score=0.7, reasoning="Honest about the missing evidence."),
    )

    evaluation = chat_evaluator_service.evaluate_research_tool_assisted_output(
        question="What can we conclude from the current material?",
        expected_json={"allow_degraded_without_sources": True},
        output_json={
            "answer": "There is not enough grounded material yet to reach a firm conclusion.",
            "sources": [],
            "tool_steps": [
                {"tool_name": "list_workspace_documents", "summary": "Checked the material."},
            ],
        },
        trace_metadata={"degraded_reason": "no_documents"},
    )

    checks = evaluation.details_json["rule_evaluation"]["checks"]
    assert checks["tool_steps_present"]["passed"] is True
    assert checks["source_present"]["passed"] is False
    assert checks["honest_degraded_path"]["passed"] is True
    assert checks["degraded_reason_visible"]["passed"] is True
    assert evaluation.passed is True


def test_evaluate_research_analysis_run_regression_passes_for_visible_completed_run() -> None:
    review = chat_evaluator_service.evaluate_research_analysis_run_regression(
        run_json={
            "status": "completed",
            "trace_id": "trace-1",
            "answer": "The strongest signal is pricing pressure.",
            "sources": [{"document_title": "market-notes.txt"}],
            "tool_steps": [
                {"tool_name": "list_workspace_documents", "summary": "Checked the workspace."},
            ],
            "run_memory": {
                "summary": "Pricing pressure is the strongest signal so far.",
                "recommended_next_step": "Generate a formal summary next.",
            },
            "resumed_from_run_id": None,
        },
        trace_response_json={},
        trace_metadata={"prompt": "analysis prompt"},
        trace_type="research_tool_assisted_run",
    )

    assert review["baseline_version"] == RESEARCH_ANALYSIS_RUN_REGRESSION_BASELINE_VERSION
    assert review["passed"] is True
    assert review["issues"] == []


def test_evaluate_research_analysis_run_regression_detects_missing_resumed_memory_visibility() -> None:
    review = chat_evaluator_service.evaluate_research_analysis_run_regression(
        run_json={
            "status": "degraded",
            "trace_id": "trace-2",
            "answer": "There is not enough grounded material yet.",
            "sources": [],
            "tool_steps": [{"tool_name": "search_documents", "summary": "Looked for matches."}],
            "run_memory": {
                "summary": "No grounded material yet.",
                "recommended_next_step": "Upload more evidence.",
            },
            "degraded_reason": "no_grounded_matches",
            "resumed_from_run_id": "run-1",
        },
        trace_response_json={},
        trace_metadata={
            "prompt": "analysis prompt",
            "degraded_reason": "no_grounded_matches",
        },
        trace_type="research_tool_assisted_run",
    )

    assert review["passed"] is False
    assert "missing_resumed_memory_visibility" in review["issues"]



def test_evaluate_research_analysis_run_regression_passes_for_visible_external_context_run() -> None:
    review = chat_evaluator_service.evaluate_research_analysis_run_regression(
        run_json={
            "status": "completed",
            "mode": "research_external_context",
            "trace_id": "trace-external-1",
            "answer": "工作区资料与已授权外部信息都指向同一个价格压力信号。",
            "sources": [
                {"document_title": "workspace-notes.txt", "source_kind": "workspace_document"},
                {"document_title": "Analyst note", "source_kind": "external_context"},
            ],
            "tool_steps": [
                {"tool_name": "research_external_context", "summary": "已命中外部信息。"},
            ],
            "run_memory": {
                "summary": "价格压力仍然是最强信号。",
                "recommended_next_step": "整理正式输出。",
            },
            "resumed_from_run_id": None,
            "external_resource_snapshot_id": "snapshot-auto-1",
        },
        trace_response_json={
            "connector_id": "research_external_context",
            "connector_consent_state": "granted",
            "external_context_used": True,
            "external_match_count": 1,
            "external_resource_snapshot_id": "snapshot-auto-1",
            "context_selection_mode": "mcp_resource",
            "mcp_server_id": "research_context_stdio",
            "mcp_resource_id": "research.context.digest",
            "mcp_resource_uri": "resource://research.context.digest",
            "mcp_resource_display_name": "Research 外部上下文摘要",
            "mcp_transport": "stdio_process",
            "mcp_read_status": "used",
        },
        trace_metadata={"prompt": "analysis prompt"},
        trace_type="research_external_context_run",
    )

    assert review["passed"] is True
    assert review["issues"] == []
    assert review["signals"]["connector_id"] == "research_external_context"
    assert review["signals"]["external_context_used"] is True
    assert review["signals"]["external_match_count"] == 1
    assert review["signals"]["resource_selection_mode"] == "auto"
    assert review["signals"]["context_selection_mode"] == "mcp_resource"
    assert review["signals"]["mcp_resource_id"] == "research.context.digest"


def test_evaluate_research_analysis_run_regression_passes_for_explicit_snapshot_selection() -> None:
    review = chat_evaluator_service.evaluate_research_analysis_run_regression(
        run_json={
            "status": "completed",
            "mode": "research_external_context",
            "trace_id": "trace-external-2",
            "answer": "显式选择的外部资源快照确认了工作区里的判断。",
            "sources": [
                {"document_title": "workspace-notes.txt", "source_kind": "workspace_document"},
                {"document_title": "Selected analyst note", "source_kind": "external_context"},
            ],
            "tool_steps": [
                {"tool_name": "research_external_context", "summary": "已显式复用外部资源快照。"},
            ],
            "run_memory": {
                "summary": "显式选择的快照强化了价格压力判断。",
                "recommended_next_step": "生成正式研究结论。",
            },
            "selected_external_resource_snapshot_id": "snapshot-explicit-1",
            "external_resource_snapshot_id": "snapshot-explicit-1",
        },
        trace_response_json={
            "connector_id": "research_external_context",
            "connector_consent_state": "granted",
            "external_context_used": True,
            "external_match_count": 1,
            "selected_external_resource_snapshot_id": "snapshot-explicit-1",
            "external_resource_snapshot_id": "snapshot-explicit-1",
            "context_selection_mode": "snapshot",
            "mcp_transport": "stdio_process",
            "mcp_read_status": "snapshot_reused",
        },
        trace_metadata={"prompt": "analysis prompt"},
        trace_type="research_external_context_run",
    )

    assert review["passed"] is True
    assert review["issues"] == []
    assert review["signals"]["resource_selection_mode"] == "explicit"
    assert review["signals"]["selected_external_resource_snapshot_id"] == "snapshot-explicit-1"
    assert review["signals"]["external_resource_snapshot_id"] == "snapshot-explicit-1"
    assert review["signals"]["context_selection_mode"] == "snapshot"


def test_evaluate_research_analysis_run_regression_detects_revoked_consent_visibility_gap() -> None:
    review = chat_evaluator_service.evaluate_research_analysis_run_regression(
        run_json={
            "status": "degraded",
            "mode": "research_external_context",
            "trace_id": "trace-external-3",
            "answer": "这次只能回退到工作区资料。",
            "sources": [],
            "tool_steps": [
                {"tool_name": "research_external_context", "summary": "授权已撤销。"},
            ],
            "run_memory": {
                "summary": "授权撤销，未使用外部资源。",
                "recommended_next_step": "重新授权后再试。",
            },
        },
        trace_response_json={
            "connector_id": "research_external_context",
            "connector_consent_state": "revoked",
            "external_context_used": False,
            "external_match_count": 0,
            "degraded_reason": "connector_consent_required",
            "context_selection_mode": "mcp_resource",
            "mcp_server_id": "research_context_stdio",
            "mcp_resource_id": "research.context.digest",
            "mcp_resource_uri": "resource://research.context.digest",
            "mcp_resource_display_name": "Research 外部上下文摘要",
            "mcp_transport": "stdio_process",
            "mcp_read_status": "consent_required",
        },
        trace_metadata={"prompt": "analysis prompt"},
        trace_type="research_external_context_run",
    )

    assert review["passed"] is False
    assert "inconsistent_connector_consent_lifecycle" in review["issues"]
    assert "inconsistent_remote_mcp_outcome_visibility" in review["issues"]


def test_evaluate_research_analysis_run_regression_detects_missing_mcp_visibility() -> None:
    review = chat_evaluator_service.evaluate_research_analysis_run_regression(
        run_json={
            "status": "degraded",
            "mode": "research_external_context",
            "trace_id": "trace-external-4",
            "answer": "这次只能回退到工作区资料。",
            "sources": [],
            "tool_steps": [
                {"tool_name": "research_external_context", "summary": "MCP 资源暂时不可用。"},
            ],
            "run_memory": {
                "summary": "MCP 资源暂时不可用。",
                "recommended_next_step": "稍后重试。",
            },
            "degraded_reason": "external_context_unavailable",
        },
        trace_response_json={
            "connector_id": "research_external_context",
            "connector_consent_state": "granted",
            "external_context_used": False,
            "external_match_count": 0,
            "context_selection_mode": "mcp_resource",
        },
        trace_metadata={"prompt": "analysis prompt"},
        trace_type="research_external_context_run",
    )

    assert review["passed"] is False
    assert "missing_mcp_server_visibility" in review["issues"]
    assert "missing_mcp_resource_visibility" in review["issues"]
    assert "missing_mcp_transport_visibility" in review["issues"]
    assert "missing_remote_mcp_read_status_visibility" in review["issues"]


def test_evaluate_research_analysis_run_regression_requires_transport_error_on_remote_failure() -> None:
    review = chat_evaluator_service.evaluate_research_analysis_run_regression(
        run_json={
            "status": "degraded",
            "mode": "research_external_context",
            "trace_id": "trace-external-5",
            "answer": "这次只能回退到工作区资料。",
            "sources": [],
            "tool_steps": [
                {"tool_name": "research_external_context", "summary": "远程 MCP 暂不可用。"},
            ],
            "run_memory": {
                "summary": "远程 MCP 暂不可用。",
                "recommended_next_step": "稍后重试。",
            },
            "degraded_reason": "external_context_unavailable",
        },
        trace_response_json={
            "connector_id": "research_external_context",
            "connector_consent_state": "granted",
            "external_context_used": False,
            "external_match_count": 0,
            "context_selection_mode": "mcp_resource",
            "mcp_server_id": "research_context_stdio",
            "mcp_resource_id": "research.context.digest",
            "mcp_resource_uri": "resource://research.context.digest",
            "mcp_resource_display_name": "Research 外部上下文摘要",
            "mcp_transport": "stdio_process",
            "mcp_read_status": "transport_unavailable",
        },
        trace_metadata={"prompt": "analysis prompt"},
        trace_type="research_external_context_run",
    )

    assert review["passed"] is False
    assert "missing_mcp_transport_error_visibility" in review["issues"]
