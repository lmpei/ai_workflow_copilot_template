from app.schemas.scenario import (
    MODULE_TYPE_RESEARCH,
    merge_module_config,
)


def resolve_workspace_module_contract(
    *,
    current_module_type: str | None = None,
    current_module_config_json: dict[str, object] | None = None,
    requested_module_type: str | None = None,
    requested_module_config_json: dict[str, object] | None = None,
    default_module_type: str = MODULE_TYPE_RESEARCH,
) -> tuple[str, dict[str, object]]:
    resolved_module_type = (
        requested_module_type
        or current_module_type
        or default_module_type
    )

    module_type_changed = resolved_module_type != current_module_type

    if requested_module_config_json is not None:
        resolved_module_config_json = merge_module_config(
            resolved_module_type,
            requested_module_config_json,
        )
    elif current_module_config_json is not None and not module_type_changed:
        resolved_module_config_json = merge_module_config(
            resolved_module_type,
            current_module_config_json,
        )
    else:
        resolved_module_config_json = merge_module_config(resolved_module_type, None)

    return resolved_module_type, resolved_module_config_json
