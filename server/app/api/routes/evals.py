from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.eval import EvalDatasetCreate, EvalDatasetResponse, EvalRunCreate, EvalRunResponse
from app.services import eval_service
from app.services.eval_service import EvalAccessError, EvalValidationError

router = APIRouter()


@router.post(
    "/workspaces/{workspace_id}/evals/datasets",
    response_model=EvalDatasetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_eval_dataset(
    workspace_id: str,
    payload: EvalDatasetCreate,
    current_user: User = Depends(get_current_user),
) -> EvalDatasetResponse:
    try:
        return eval_service.create_eval_dataset(
            workspace_id=workspace_id,
            user_id=current_user.id,
            payload=payload,
        )
    except EvalAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except EvalValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get(
    "/workspaces/{workspace_id}/evals/datasets",
    response_model=list[EvalDatasetResponse],
)
async def list_eval_datasets(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
) -> list[EvalDatasetResponse]:
    try:
        return eval_service.list_workspace_eval_datasets(
            workspace_id=workspace_id,
            user_id=current_user.id,
        )
    except EvalAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post(
    "/workspaces/{workspace_id}/evals/runs",
    response_model=EvalRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_eval_run(
    workspace_id: str,
    payload: EvalRunCreate,
    current_user: User = Depends(get_current_user),
) -> EvalRunResponse:
    try:
        return eval_service.create_eval_run(
            workspace_id=workspace_id,
            user_id=current_user.id,
            payload=payload,
        )
    except EvalAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except EvalValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/evals/runs/{eval_run_id}", response_model=EvalRunResponse)
async def get_eval_run(
    eval_run_id: str,
    current_user: User = Depends(get_current_user),
) -> EvalRunResponse:
    eval_run = eval_service.get_eval_run(eval_run_id=eval_run_id, user_id=current_user.id)
    if eval_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Eval run not found")
    return eval_run
