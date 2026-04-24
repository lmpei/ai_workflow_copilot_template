from app.services.ai_hot_tracker_replay_service import run_ai_hot_tracker_replay_suite


def _failure_lines() -> list[str]:
    suite = run_ai_hot_tracker_replay_suite()
    failures: list[str] = []
    for case in suite.cases:
        for step in case.steps:
            for finding in step.findings:
                if finding.status == "fail":
                    failures.append(
                        f"{case.case_id}/{step.label}/{finding.code}: {finding.summary}"
                    )
    return failures


def test_ai_hot_tracker_replay_suite_passes_core_cases() -> None:
    suite = run_ai_hot_tracker_replay_suite()
    assert suite.total_case_count >= 5
    assert suite.failed_case_count == 0, _failure_lines()


def test_ai_hot_tracker_replay_suite_covers_threshold_and_replacement_paths() -> None:
    suite = run_ai_hot_tracker_replay_suite()
    case_by_id = {case.case_id: case for case in suite.cases}

    threshold_case = case_by_id["threshold-driven-meaningful-update"]
    threshold_step = next(step for step in threshold_case.steps if step.label == "threshold-run")
    assert threshold_step.delta.change_state == "meaningful_update"
    assert threshold_step.delta.notify_reason == "新增中高优先级信号达到阈值 2"

    replacement_case = case_by_id["replacement-signal-creates-superseded-memory"]
    replacement_step = next(step for step in replacement_case.steps if step.label == "mode-run")
    replaced_memory = next(
        memory
        for memory in replacement_step.event_memories
        if memory.title == "OpenAI launches ChatGPT agent tools beta"
    )
    assert replaced_memory.activity_state == "replaced"
    assert replaced_memory.superseded_by_event_id is not None
