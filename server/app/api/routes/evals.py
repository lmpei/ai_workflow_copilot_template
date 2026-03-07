from fastapi import APIRouter, HTTPException, status

from app.schemas.eval import EvalRunRequest
from app.services.eval_service import get_eval_module_status

router = APIRouter()


@router.post("/workspaces/{workspace_id}/evals/run", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def run_eval(workspace_id: str, payload: EvalRunRequest) -> dict:
    detail = get_eval_module_status()
    detail["workspace_id"] = workspace_id
    detail["eval_name"] = payload.eval_name
    detail["dataset_name"] = payload.dataset_name
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=detail)


@router.get("/workspaces/{workspace_id}/evals", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def list_evals(workspace_id: str) -> dict:
    detail = get_eval_module_status()
    detail["workspace_id"] = workspace_id
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=detail)
