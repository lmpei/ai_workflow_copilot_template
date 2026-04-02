from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.research_analysis_review import ResearchAnalysisReviewResponse
from app.schemas.research_analysis_run import ResearchAnalysisRunCreate, ResearchAnalysisRunResponse
from app.schemas.research_external_resource_snapshot import ResearchExternalResourceSnapshotResponse
from app.services.research_analysis_review_service import list_workspace_research_analysis_review
from app.services.research_external_resource_snapshot_service import (
    ResearchExternalResourceSnapshotAccessError,
    ResearchExternalResourceSnapshotValidationError,
    list_workspace_research_external_resource_snapshots,
)
from app.services.research_analysis_run_service import (
    ResearchAnalysisRunAccessError,
    ResearchAnalysisRunExecutionError,
    ResearchAnalysisRunQueueError,
    ResearchAnalysisRunValidationError,
    create_research_analysis_run,
    get_research_analysis_run,
    list_workspace_research_analysis_runs,
)

router = APIRouter()


@router.post(
    "/workspaces/{workspace_id}/research-analysis-runs",
    response_model=ResearchAnalysisRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_run(
    workspace_id: str,
    payload: ResearchAnalysisRunCreate,
    current_user: User = Depends(get_current_user),
) -> ResearchAnalysisRunResponse:
    try:
        return await create_research_analysis_run(
            workspace_id=workspace_id,
            user_id=current_user.id,
            payload=payload,
        )
    except ResearchAnalysisRunAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ResearchAnalysisRunValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except (ResearchAnalysisRunQueueError, ResearchAnalysisRunExecutionError) as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error


@router.get(
    "/workspaces/{workspace_id}/research-analysis-runs",
    response_model=list[ResearchAnalysisRunResponse],
)
async def list_runs(
    workspace_id: str,
    limit: int = Query(default=12, ge=1, le=20),
    current_user: User = Depends(get_current_user),
) -> list[ResearchAnalysisRunResponse]:
    try:
        return list_workspace_research_analysis_runs(
            workspace_id=workspace_id,
            user_id=current_user.id,
            limit=limit,
        )
    except ResearchAnalysisRunAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ResearchAnalysisRunValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get(
    "/workspaces/{workspace_id}/research-external-resource-snapshots",
    response_model=list[ResearchExternalResourceSnapshotResponse],
)
async def list_resource_snapshots(
    workspace_id: str,
    limit: int = Query(default=8, ge=1, le=20),
    current_user: User = Depends(get_current_user),
) -> list[ResearchExternalResourceSnapshotResponse]:
    try:
        return list_workspace_research_external_resource_snapshots(
            workspace_id=workspace_id,
            user_id=current_user.id,
            limit=limit,
        )
    except ResearchExternalResourceSnapshotAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ResearchExternalResourceSnapshotValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get(
    "/workspaces/{workspace_id}/research-analysis-runs/review",
    response_model=ResearchAnalysisReviewResponse,
)
async def get_run_review(
    workspace_id: str,
    limit: int = Query(default=8, ge=1, le=20),
    current_user: User = Depends(get_current_user),
) -> ResearchAnalysisReviewResponse:
    try:
        return list_workspace_research_analysis_review(
            workspace_id=workspace_id,
            user_id=current_user.id,
            limit=limit,
        )
    except ResearchAnalysisRunAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ResearchAnalysisRunValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/research-analysis-runs/{run_id}", response_model=ResearchAnalysisRunResponse)
async def get_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
) -> ResearchAnalysisRunResponse:
    run = get_research_analysis_run(run_id=run_id, user_id=current_user.id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research analysis run not found")
    return run
