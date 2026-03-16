import pytest

from app.services.scenario_eval_service import (
    ScenarioEvalConfigError,
    resolve_scenario_eval_config,
    resolve_scenario_eval_prompt,
)


def test_resolve_scenario_eval_config_defaults_to_workspace_module() -> None:
    config = resolve_scenario_eval_config(
        workspace_module_type="support",
        config_json=None,
    )

    assert config == {
        "module_type": "support",
        "scenario_task_type": "reply_draft",
        "quality_baseline": "grounded_support",
        "pass_threshold": 0.75,
    }


def test_resolve_scenario_eval_config_rejects_mismatched_module() -> None:
    with pytest.raises(
        ScenarioEvalConfigError,
        match="does not match workspace module",
    ):
        resolve_scenario_eval_config(
            workspace_module_type="job",
            config_json={"module_type": "research"},
        )


def test_resolve_scenario_eval_prompt_uses_module_specific_field() -> None:
    prompt = resolve_scenario_eval_prompt(
        input_json={"customer_issue": "Customer cannot log in"},
        scenario_config={
            "module_type": "support",
            "scenario_task_type": "ticket_summary",
            "quality_baseline": "grounded_support",
            "pass_threshold": 0.75,
        },
    )

    assert prompt == "Customer cannot log in"
