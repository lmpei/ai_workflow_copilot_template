from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.task import TaskControlRequest, TaskCreate, TaskResponse
from app.services import task_service
from app.services.task_service import (
    TaskAccessError,
    TaskControlError,
    TaskQueueError,
    TaskValidationError,
)

router = APIRouter()


@router.post(
    "/workspaces/{workspace_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    workspace_id: str,
    payload: TaskCreate,
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    try:
        return await task_service.create_task(
            workspace_id=workspace_id,
            user_id=current_user.id,
            payload=payload,
        )
    except TaskAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except TaskValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except TaskQueueError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error


@router.post("/tasks/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(
    task_id: str,
    payload: TaskControlRequest | None = None,
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    try:
        return task_service.cancel_task(
            task_id=task_id,
            user_id=current_user.id,
            payload=payload,
        )
    except TaskAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except TaskControlError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.post("/tasks/{task_id}/retry", response_model=TaskResponse)
async def retry_task(
    task_id: str,
    payload: TaskControlRequest | None = None,
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    try:
        return await task_service.retry_task(
            task_id=task_id,
            user_id=current_user.id,
            payload=payload,
        )
    except TaskAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except TaskControlError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except TaskQueueError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    task = task_service.get_task(task_id=task_id, user_id=current_user.id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到任务")
    return task


@router.get("/workspaces/{workspace_id}/tasks", response_model=list[TaskResponse])
async def list_tasks(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
) -> list[TaskResponse]:
    try:
        return task_service.list_workspace_tasks(
            workspace_id=workspace_id,
            user_id=current_user.id,
        )
    except TaskAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
