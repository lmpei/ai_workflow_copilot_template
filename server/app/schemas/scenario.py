from copy import deepcopy
from typing import Literal, cast

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

_SCENARIO_REGISTRY: dict[str, dict[str, object]] = {
    MODULE_TYPE_RESEARCH: {
        "module_type": MODULE_TYPE_RESEARCH,
        "title": "Research Assistant",
        "short_label": "Research",
        "description": "Grounded retrieval, comparison, summarization, and report generation.",
        "work_object": "Workspace-scoped document sets, evidence, and open research questions.",
        "primary_output": "Evidence-backed synthesis and workspace reports.",
        "core_capabilities": [
            "grounded retrieval",
            "multi-document summarization",
            "viewpoint comparison",
            "report generation",
        ],
        "not_responsible_for": [
            "ticket triage",
            "reply drafting",
            "candidate-to-role matching",
        ],
        "eval_input_label": "Questions or research goals",
        "eval_prompt_field": "question",
        "default_eval_task_type": "research_summary",
        "quality_baseline": "grounded_research",
        "pass_threshold": 0.7,
        "result_type": "research_report",
        "features": ["documents", "grounded_chat", "tasks", "evals"],
        "tasks": {
            "research_summary": {
                "task_type": "research_summary",
                "label": "Research Summary",
                "input_field": "goal",
                "eval_prompt_placeholder": "One research question per line",
            },
            "workspace_report": {
                "task_type": "workspace_report",
                "label": "Workspace Report",
                "input_field": "goal",
                "eval_prompt_placeholder": "One report prompt per line",
            },
        },
    },
    MODULE_TYPE_SUPPORT: {
        "module_type": MODULE_TYPE_SUPPORT,
        "title": "Support Copilot",
        "short_label": "Support",
        "description": "Knowledge Q&A, ticket classification, drafting, and escalation guidance.",
        "work_object": "Support cases, tickets, and knowledge-base context.",
        "primary_output": "Grounded case summaries, reply drafts, and escalation guidance.",
        "core_capabilities": [
            "knowledge-base Q&A",
            "ticket classification",
            "reply drafting",
            "escalation guidance",
        ],
        "not_responsible_for": [
            "long-form research synthesis",
            "multi-document comparison across a broad corpus",
            "hiring workflow evaluation",
        ],
        "eval_input_label": "Customer issues or ticket prompts",
        "eval_prompt_field": "customer_issue",
        "default_eval_task_type": "reply_draft",
        "quality_baseline": "grounded_support",
        "pass_threshold": 0.75,
        "result_type": "support_case_summary",
        "features": ["knowledge_base", "reply_drafts", "tasks", "evals"],
        "tasks": {
            "ticket_summary": {
                "task_type": "ticket_summary",
                "label": "Ticket Summary",
                "input_field": "customer_issue",
                "eval_prompt_placeholder": "One support issue per line",
            },
            "reply_draft": {
                "task_type": "reply_draft",
                "label": "Reply Draft",
                "input_field": "customer_issue",
                "eval_prompt_placeholder": "One customer issue per line",
            },
        },
    },
    MODULE_TYPE_JOB: {
        "module_type": MODULE_TYPE_JOB,
        "title": "Job Assistant",
        "short_label": "Job",
        "description": "JD parsing, resume matching, gap analysis, and application workflows.",
        "work_object": "Hiring materials such as job descriptions, resumes, and fit criteria.",
        "primary_output": "Structured job summaries, match assessments, and next-step recommendations.",
        "core_capabilities": [
            "structured extraction",
            "resume matching",
            "gap analysis",
            "application workflow support",
        ],
        "not_responsible_for": [
            "support-case handling",
            "knowledge-base reply generation",
            "broad research report synthesis",
        ],
        "eval_input_label": "Role prompts or hiring focus lines",
        "eval_prompt_field": "target_role",
        "default_eval_task_type": "resume_match",
        "quality_baseline": "grounded_job",
        "pass_threshold": 0.75,
        "result_type": "job_match_summary",
        "features": ["document_intake", "structured_extraction", "tasks", "evals"],
        "tasks": {
            "jd_summary": {
                "task_type": "jd_summary",
                "label": "JD Summary",
                "input_field": "target_role",
                "eval_prompt_placeholder": "One target role or job focus per line",
            },
            "resume_match": {
                "task_type": "resume_match",
                "label": "Resume Match",
                "input_field": "target_role",
                "eval_prompt_placeholder": "One target role per line",
            },
        },
    },
}

ScenarioTaskRegistry = dict[str, dict[str, object]]


class ScenarioTaskDefinitionResponse(BaseModel):
    task_type: ScenarioTaskType
    label: str
    input_field: str
    eval_prompt_placeholder: str


class ScenarioModuleDefinitionResponse(BaseModel):
    module_type: ModuleType
    title: str
    short_label: str
    description: str
    work_object: str
    primary_output: str
    core_capabilities: list[str] = Field(default_factory=list)
    not_responsible_for: list[str] = Field(default_factory=list)
    entry_task_types: list[ScenarioTaskType] = Field(default_factory=list)
    task_labels: dict[ScenarioTaskType, str] = Field(default_factory=dict)
    eval_input_label: str
    eval_prompt_field: str
    default_eval_task_type: ScenarioTaskType
    quality_baseline: str
    pass_threshold: float
    tasks: list[ScenarioTaskDefinitionResponse] = Field(default_factory=list)


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


def _deepcopy_registry_module(module_type: str) -> dict[str, object]:
    if module_type not in _SCENARIO_REGISTRY:
        raise ValueError(f"Unsupported module type: {module_type}")
    return deepcopy(_SCENARIO_REGISTRY[module_type])


def _get_registry_tasks(module_data: dict[str, object]) -> ScenarioTaskRegistry:
    tasks = module_data.get("tasks")
    if not isinstance(tasks, dict):
        raise ValueError("Scenario registry module is missing task definitions")
    return cast(ScenarioTaskRegistry, deepcopy(tasks))


def _get_registry_string_list(module_data: dict[str, object], key: str) -> list[str]:
    raw_values = module_data.get(key)
    if not isinstance(raw_values, list):
        return []
    return [value for value in raw_values if isinstance(value, str)]


def _get_registry_float(module_data: dict[str, object], key: str) -> float:
    raw_value = module_data.get(key)
    if isinstance(raw_value, (int, float)):
        return float(raw_value)
    raise ValueError(f"Scenario registry field {key} must be numeric")


def _iter_registry_tasks() -> list[tuple[str, dict[str, object]]]:
    task_entries: list[tuple[str, dict[str, object]]] = []
    for module_data in _SCENARIO_REGISTRY.values():
        task_entries.extend(
            (task_type, deepcopy(task_definition))
            for task_type, task_definition in _get_registry_tasks(module_data).items()
        )
    return task_entries


def is_supported_module_type(module_type: str) -> bool:
    return module_type in SUPPORTED_MODULE_TYPES


def is_supported_scenario_task_type(task_type: str) -> bool:
    return any(task_type == candidate_task_type for candidate_task_type, _ in _iter_registry_tasks())


def get_scenario_task_definition(task_type: str) -> dict[str, object]:
    for candidate_task_type, task_definition in _iter_registry_tasks():
        if candidate_task_type == task_type:
            return task_definition
    raise ValueError(f"Unsupported task type: {task_type}")


def get_scenario_task_label(task_type: str) -> str:
    task_definition = get_scenario_task_definition(task_type)
    return str(task_definition["label"])


def get_scenario_task_input_field(task_type: str) -> str:
    task_definition = get_scenario_task_definition(task_type)
    return str(task_definition["input_field"])


def get_scenario_task_module_type(task_type: str) -> str:
    for module_type, module_data in _SCENARIO_REGISTRY.items():
        if task_type in _get_registry_tasks(module_data):
            return module_type
    raise ValueError(f"Unsupported task type: {task_type}")


def get_supported_scenario_task_types(module_type: str) -> tuple[str, ...]:
    module_definition = _deepcopy_registry_module(module_type)
    return tuple(_get_registry_tasks(module_definition).keys())


def get_default_module_config(module_type: str) -> dict[str, object]:
    module_definition = _deepcopy_registry_module(module_type)
    return {
        "entry_task_types": list(_get_registry_tasks(module_definition).keys()),
        "result_type": module_definition["result_type"],
        "features": _get_registry_string_list(module_definition, "features"),
    }


def get_scenario_module_definition(module_type: str) -> dict[str, object]:
    module_definition = _deepcopy_registry_module(module_type)
    task_definitions = _get_registry_tasks(module_definition)
    return {
        "module_type": module_definition["module_type"],
        "title": module_definition["title"],
        "short_label": module_definition["short_label"],
        "description": module_definition["description"],
        "work_object": module_definition["work_object"],
        "primary_output": module_definition["primary_output"],
        "core_capabilities": _get_registry_string_list(module_definition, "core_capabilities"),
        "not_responsible_for": _get_registry_string_list(module_definition, "not_responsible_for"),
        "entry_task_types": list(task_definitions.keys()),
        "task_labels": {
            task_type: str(task_definition["label"])
            for task_type, task_definition in task_definitions.items()
        },
        "eval_input_label": module_definition["eval_input_label"],
        "eval_prompt_field": module_definition["eval_prompt_field"],
        "default_eval_task_type": module_definition["default_eval_task_type"],
        "quality_baseline": module_definition["quality_baseline"],
        "pass_threshold": _get_registry_float(module_definition, "pass_threshold"),
        "tasks": [
            {
                "task_type": task_type,
                "label": task_definition["label"],
                "input_field": task_definition["input_field"],
                "eval_prompt_placeholder": task_definition["eval_prompt_placeholder"],
            }
            for task_type, task_definition in task_definitions.items()
        ],
    }


def list_scenario_module_definitions() -> list[dict[str, object]]:
    return [get_scenario_module_definition(module_type) for module_type in SUPPORTED_MODULE_TYPES]


def get_default_scenario_eval_config(module_type: str) -> dict[str, object]:
    module_definition = _deepcopy_registry_module(module_type)
    return {
        "module_type": module_definition["module_type"],
        "scenario_task_type": module_definition["default_eval_task_type"],
        "quality_baseline": module_definition["quality_baseline"],
        "pass_threshold": _get_registry_float(module_definition, "pass_threshold"),
    }


def get_scenario_eval_prompt_field(module_type: str) -> str:
    module_definition = _deepcopy_registry_module(module_type)
    return str(module_definition["eval_prompt_field"])


def get_scenario_eval_input_label(module_type: str) -> str:
    module_definition = _deepcopy_registry_module(module_type)
    return str(module_definition["eval_input_label"])


def merge_module_config(
    module_type: str | None,
    module_config_json: dict[str, object] | None,
) -> dict[str, object]:
    if module_type is None:
        raise ValueError("Module type is required")
    merged = get_default_module_config(module_type)
    if module_config_json:
        merged.update(deepcopy(module_config_json))
    return merged
