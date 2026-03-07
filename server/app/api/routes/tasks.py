from fastapi import APIRouter, HTTPException, status

from app.schemas.task import TaskCreate

router = APIRouter()


@router.post("/workspaces/{workspace_id}/tasks", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def create_task(workspace_id: str, payload: TaskCreate) -> dict:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "status": "scaffolded",
            "message": "Task orchestration is planned for Phase 3 with Redis-backed workers.",
            "workspace_id": workspace_id,
            "task_type": payload.task_type,
        },
    )


@router.get("/tasks/{task_id}", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def get_task(task_id: str) -> dict:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Task lookup is a Phase 3 scaffold and is not implemented yet.",
    )


@router.get("/workspaces/{workspace_id}/tasks", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def list_tasks(workspace_id: str) -> dict:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "status": "scaffolded",
            "message": "Workspace task listing is planned for Phase 3 with task persistence.",
            "workspace_id": workspace_id,
        },
    )
