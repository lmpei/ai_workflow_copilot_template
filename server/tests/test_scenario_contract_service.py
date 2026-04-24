from app.services.scenario_contract_service import resolve_workspace_module_contract


def test_resolve_workspace_module_contract_defaults_to_research() -> None:
    module_type, module_config_json = resolve_workspace_module_contract()

    assert module_type == "research"
    assert module_config_json["entry_task_types"] == [
        "research_summary",
        "workspace_report",
    ]
    assert module_config_json["result_type"] == "ai_frontier_research_record"
    assert module_config_json["tracking_profile"]["topic"] == "AI 模型、产品、工具、论文、开源与商业变化"


def test_resolve_workspace_module_contract_merges_requested_config() -> None:
    module_type, module_config_json = resolve_workspace_module_contract(
        requested_module_type="support",
        requested_module_config_json={"features": ["reply_drafts"], "custom_flag": True},
    )

    assert module_type == "support"
    assert module_config_json["entry_task_types"] == [
        "ticket_summary",
        "reply_draft",
    ]
    assert module_config_json["features"] == ["reply_drafts"]
    assert module_config_json["custom_flag"] is True


def test_resolve_workspace_module_contract_resets_defaults_when_module_changes() -> None:
    module_type, module_config_json = resolve_workspace_module_contract(
        current_module_type="research",
        current_module_config_json={"entry_task_types": ["custom_research"], "custom_flag": True},
        requested_module_type="job",
    )

    assert module_type == "job"
    assert module_config_json["entry_task_types"] == [
        "jd_summary",
        "resume_match",
    ]
    assert module_config_json["result_type"] == "job_match_summary"
    assert "custom_flag" not in module_config_json
