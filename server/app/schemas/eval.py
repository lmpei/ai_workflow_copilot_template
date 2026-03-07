from datetime import datetime

from pydantic import BaseModel, Field


class EvalRunRequest(BaseModel):
    eval_name: str
    dataset_name: str
    input: dict = Field(default_factory=dict)


class EvalResponse(BaseModel):
    id: str
    workspace_id: str
    eval_name: str
    dataset_name: str
    metric_json: dict
    created_at: datetime
