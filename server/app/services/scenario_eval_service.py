from app.schemas.scenario import (
    get_default_scenario_eval_config,
    get_scenario_eval_prompt_field,
    get_scenario_task_module_type,
    get_supported_scenario_task_types,
    is_supported_module_type,
)


class ScenarioEvalConfigError(ValueError):
    pass


def resolve_scenario_eval_config(
    *,
    workspace_module_type: str,
    config_json: dict[str, object] | None,
) -> dict[str, object]:
    if not is_supported_module_type(workspace_module_type):
        raise ScenarioEvalConfigError(f"Unsupported module type: {workspace_module_type}")

    resolved = get_default_scenario_eval_config(workspace_module_type)
    if config_json:
        resolved.update(config_json)

    module_type = resolved.get("module_type")
    if not isinstance(module_type, str) or not is_supported_module_type(module_type):
        raise ScenarioEvalConfigError("Scenario eval config must include a supported module_type")
    if module_type != workspace_module_type:
        raise ScenarioEvalConfigError(
            "Scenario eval config module_type "
            f"{module_type} does not match workspace module {workspace_module_type}",
        )

    scenario_task_type = resolved.get("scenario_task_type")
    if not isinstance(scenario_task_type, str):
        raise ScenarioEvalConfigError(
            "Scenario eval config must include a scenario_task_type",
        )
    if scenario_task_type not in get_supported_scenario_task_types(module_type):
        raise ScenarioEvalConfigError(
            f"Task type {scenario_task_type} is not supported for scenario module {module_type}",
        )
    if get_scenario_task_module_type(scenario_task_type) != module_type:
        raise ScenarioEvalConfigError(
            f"Task type {scenario_task_type} is not registered for scenario module {module_type}",
        )

    quality_baseline = resolved.get("quality_baseline")
    if not isinstance(quality_baseline, str) or not quality_baseline.strip():
        raise ScenarioEvalConfigError(
            "Scenario eval config must include a quality_baseline",
        )

    pass_threshold = resolved.get("pass_threshold")
    if not isinstance(pass_threshold, int | float):
        raise ScenarioEvalConfigError(
            "Scenario eval config must include a numeric pass_threshold",
        )

    return {
        "module_type": module_type,
        "scenario_task_type": scenario_task_type,
        "quality_baseline": quality_baseline.strip(),
        "pass_threshold": max(0.0, min(float(pass_threshold), 1.0)),
    }


def resolve_scenario_eval_prompt(
    *,
    input_json: dict[str, object],
    scenario_config: dict[str, object],
) -> str:
    module_type = scenario_config["module_type"]
    if not isinstance(module_type, str) or not is_supported_module_type(module_type):
        raise ScenarioEvalConfigError("Scenario eval config must include a supported module_type")

    prompt_field = get_scenario_eval_prompt_field(module_type)
    value = input_json.get(prompt_field)
    if isinstance(value, str) and value.strip():
        return value.strip()

    raise ScenarioEvalConfigError("Scenario eval case input is missing a usable prompt")


def build_scenario_summary_fields(scenario_config: dict[str, object]) -> dict[str, object]:
    return {
        "module_type": scenario_config["module_type"],
        "scenario_task_type": scenario_config["scenario_task_type"],
        "quality_baseline": scenario_config["quality_baseline"],
        "pass_threshold": scenario_config["pass_threshold"],
    }


def build_scenario_metadata_json(
    *,
    scenario_config: dict[str, object],
    metadata_json: dict[str, object],
) -> dict[str, object]:
    return {
        "module_type": scenario_config["module_type"],
        "scenario_task_type": scenario_config["scenario_task_type"],
        **metadata_json,
    }