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
        "description": "基于 grounded 检索完成比较、总结与报告生成。",
        "work_object": "工作区范围内的文档集合、证据和开放研究问题。",
        "primary_output": "有证据支撑的综合结论与工作区报告。",
        "core_capabilities": [
            "grounded 检索",
            "多文档总结",
            "观点比较",
            "报告生成",
        ],
        "not_responsible_for": [
            "工单分诊",
            "回复草稿",
            "候选人与岗位匹配",
        ],
        "eval_input_label": "研究问题或研究目标",
        "eval_prompt_field": "question",
        "default_eval_task_type": "research_summary",
        "quality_baseline": "grounded_research",
        "pass_threshold": 0.7,
        "result_type": "research_report",
        "features": ["documents", "grounded_chat", "tasks", "evals"],
        "tasks": {
            "research_summary": {
                "task_type": "research_summary",
                "label": "研究摘要",
                "input_field": "goal",
                "eval_prompt_placeholder": "每行一个研究问题",
            },
            "workspace_report": {
                "task_type": "workspace_report",
                "label": "工作区报告",
                "input_field": "goal",
                "eval_prompt_placeholder": "每行一个报告提示",
            },
        },
    },
    MODULE_TYPE_SUPPORT: {
        "module_type": MODULE_TYPE_SUPPORT,
        "title": "Support Copilot",
        "short_label": "Support",
        "description": "知识问答、工单分类、回复草稿与升级指引。",
        "work_object": "支持案例、工单和知识库上下文。",
        "primary_output": "grounded 案例摘要、回复草稿和升级指引。",
        "core_capabilities": [
            "知识库问答",
            "工单分类",
            "回复草稿",
            "升级指引",
        ],
        "not_responsible_for": [
            "长篇研究综合",
            "跨大语料的多文档比较",
            "招聘流程评估",
        ],
        "eval_input_label": "客户问题或工单提示",
        "eval_prompt_field": "customer_issue",
        "default_eval_task_type": "reply_draft",
        "quality_baseline": "grounded_support",
        "pass_threshold": 0.75,
        "result_type": "support_case_summary",
        "features": ["knowledge_base", "reply_drafts", "tasks", "evals"],
        "tasks": {
            "ticket_summary": {
                "task_type": "ticket_summary",
                "label": "工单摘要",
                "input_field": "customer_issue",
                "eval_prompt_placeholder": "每行一个支持问题",
            },
            "reply_draft": {
                "task_type": "reply_draft",
                "label": "回复草稿",
                "input_field": "customer_issue",
                "eval_prompt_placeholder": "每行一个客户问题",
            },
        },
    },
    MODULE_TYPE_JOB: {
        "module_type": MODULE_TYPE_JOB,
        "title": "Job Assistant",
        "short_label": "Job",
        "description": "JD 解析、简历匹配、缺口分析和候选流程支持。",
        "work_object": "岗位说明、简历和匹配标准等招聘材料。",
        "primary_output": "结构化岗位摘要、匹配评估和下一步建议。",
        "core_capabilities": [
            "结构化提取",
            "简历匹配",
            "缺口分析",
            "候选流程支持",
        ],
        "not_responsible_for": [
            "支持案例处理",
            "知识库回复生成",
            "大范围研究报告综合",
        ],
        "eval_input_label": "岗位提示或招聘重点",
        "eval_prompt_field": "target_role",
        "default_eval_task_type": "resume_match",
        "quality_baseline": "grounded_job",
        "pass_threshold": 0.75,
        "result_type": "job_match_summary",
        "features": ["document_intake", "structured_extraction", "tasks", "evals"],
        "tasks": {
            "jd_summary": {
                "task_type": "jd_summary",
                "label": "JD 摘要",
                "input_field": "target_role",
                "eval_prompt_placeholder": "每行一个目标岗位或招聘重点",
            },
            "resume_match": {
                "task_type": "resume_match",
                "label": "简历匹配",
                "input_field": "target_role",
                "eval_prompt_placeholder": "每行一个目标岗位",
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
