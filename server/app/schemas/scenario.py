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

SCENARIO_MODULE_DEFINITIONS: dict[str, dict[str, object]] = {
    MODULE_TYPE_RESEARCH: {
        "title": "Research Assistant",
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
    },
    MODULE_TYPE_SUPPORT: {
        "title": "Support Copilot",
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
    },
    MODULE_TYPE_JOB: {
        "title": "Job Assistant",
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


def get_scenario_module_definition(module_type: str) -> dict[str, object]:
    if not is_supported_module_type(module_type):
        raise ValueError(f"Unsupported module type: {module_type}")
    return deepcopy(SCENARIO_MODULE_DEFINITIONS[module_type])


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
