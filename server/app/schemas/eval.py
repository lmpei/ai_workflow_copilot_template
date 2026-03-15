from datetime import datetime

from pydantic import BaseModel, Field

from app.models.eval_case import EvalCase
from app.models.eval_dataset import EvalDataset
from app.models.eval_run import EvalRun

SUPPORTED_EVAL_TYPES = (
    "retrieval_chat",
)


class EvalCaseCreate(BaseModel):
    input_json: dict[str, object] = Field(default_factory=dict)
    expected_json: dict[str, object] = Field(default_factory=dict)
    metadata_json: dict[str, object] = Field(default_factory=dict)


class EvalDatasetCreate(BaseModel):
    name: str
    eval_type: str
    description: str | None = None
    config_json: dict[str, object] = Field(default_factory=dict)
    cases: list[EvalCaseCreate] = Field(default_factory=list)


class EvalRunCreate(BaseModel):
    dataset_id: str


class EvalCaseResponse(BaseModel):
    id: str
    case_index: int
    input_json: dict[str, object]
    expected_json: dict[str, object]
    metadata_json: dict[str, object]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, eval_case: EvalCase) -> "EvalCaseResponse":
        return cls(
            id=eval_case.id,
            case_index=eval_case.case_index,
            input_json=eval_case.input_json,
            expected_json=eval_case.expected_json,
            metadata_json=eval_case.metadata_json,
            created_at=eval_case.created_at,
            updated_at=eval_case.updated_at,
        )


class EvalDatasetResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    eval_type: str
    description: str | None = None
    created_by: str
    config_json: dict[str, object]
    cases: list[EvalCaseResponse]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(
        cls,
        dataset: EvalDataset,
        *,
        cases: list[EvalCase],
    ) -> "EvalDatasetResponse":
        return cls(
            id=dataset.id,
            workspace_id=dataset.workspace_id,
            name=dataset.name,
            eval_type=dataset.eval_type,
            description=dataset.description,
            created_by=dataset.created_by,
            config_json=dataset.config_json,
            cases=[EvalCaseResponse.from_model(eval_case) for eval_case in cases],
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
        )


class EvalRunResponse(BaseModel):
    id: str
    workspace_id: str
    dataset_id: str
    eval_type: str
    status: str
    created_by: str
    summary_json: dict[str, object]
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    ended_at: datetime | None = None

    @classmethod
    def from_model(cls, eval_run: EvalRun) -> "EvalRunResponse":
        return cls(
            id=eval_run.id,
            workspace_id=eval_run.workspace_id,
            dataset_id=eval_run.dataset_id,
            eval_type=eval_run.eval_type,
            status=eval_run.status,
            created_by=eval_run.created_by,
            summary_json=eval_run.summary_json,
            error_message=eval_run.error_message,
            created_at=eval_run.created_at,
            started_at=eval_run.started_at,
            ended_at=eval_run.ended_at,
        )
