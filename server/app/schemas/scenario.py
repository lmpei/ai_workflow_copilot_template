from copy import deepcopy
from typing import Literal

from pydantic import BaseModel, Field

MODULE_TYPE_RESEARCH = "research"
MODULE_TYPE_SUPPORT = "support"
MODULE_TYPE_JOB = "job"

SUPPORTED_MODULE_TYPES = (
    MODULE_TYPE_RESEARCH,
    MODULE_TYPE_SUPPORT,
    MODULE_TYPE_JOB,
)

ModuleType = Literal[
    "research",
    "support",
    "job",
]
ScenarioTaskType = Literal[
    "research_summary",
    "workspace_report",
    "ticket_summary",
    "reply_draft",
    "jd_summary",
    "resume_match",
]

SCENARIO_TASK_TYPES_BY_MODULE: dict[str, tuple[str, ...]] = {
    MODULE_TYPE_RESEARCH: (
        "research_summary",
        "workspace_report",
    ),
    MODULE_TYPE_SUPPORT: (
        "ticket_summary",
        "reply_draft",
    ),
    MODULE_TYPE_JOB: (
        "jd_summary",
        "resume_match",
    ),
}

DEFAULT_MODULE_CONFIGS: dict[str, dict[str, object]] = {
    MODULE_TYPE_RESEARCH: {
        "entry_task_types": list(SCENARIO_TASK_TYPES_BY_MODULE[MODULE_TYPE_RESEARCH]),
        "result_type": "research_report",
        "features": ["documents", "grounded_chat", "tasks", "evals"],
    },
    MODULE_TYPE_SUPPORT: {
        "entry_task_types": list(SCENARIO_TASK_TYPES_BY_MODULE[MODULE_TYPE_SUPPORT]),
        "result_type": "support_case_summary",
        "features": ["knowledge_base", "reply_drafts", "tasks", "evals"],
    },
    MODULE_TYPE_JOB: {
        "entry_task_types": list(SCENARIO_TASK_TYPES_BY_MODULE[MODULE_TYPE_JOB]),
        "result_type": "job_match_summary",
        "features": ["document_intake", "structured_extraction", "tasks", "evals"],
    },
}


class ScenarioEvidenceItem(BaseModel):
    kind: str = "document_chunk"
    ref_id: str
    title: str | None = None
    snippet: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class ScenarioTaskResult(BaseModel):
    module_type: ModuleType
    task_type: ScenarioTaskType
    title: str
    summary: str
    highlights: list[str] = Field(default_factory=list)
    evidence: list[ScenarioEvidenceItem] = Field(default_factory=list)
    artifacts: dict[str, object] = Field(default_factory=dict)
    metadata: dict[str, object] = Field(default_factory=dict)


def is_supported_module_type(module_type: str) -> bool:
    return module_type in SUPPORTED_MODULE_TYPES


def get_default_module_config(module_type: str) -> dict[str, object]:
    if not is_supported_module_type(module_type):
        raise ValueError(f"Unsupported module type: {module_type}")
    return deepcopy(DEFAULT_MODULE_CONFIGS[module_type])


def get_supported_scenario_task_types(module_type: str) -> tuple[str, ...]:
    if not is_supported_module_type(module_type):
        raise ValueError(f"Unsupported module type: {module_type}")
    return SCENARIO_TASK_TYPES_BY_MODULE[module_type]


def merge_module_config(
    module_type: str,
    module_config_json: dict[str, object] | None,
) -> dict[str, object]:
    merged = get_default_module_config(module_type)
    if module_config_json:
        merged.update(deepcopy(module_config_json))
    return merged
