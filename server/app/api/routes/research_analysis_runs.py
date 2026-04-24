from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.ai_frontier_research import (
    AiFrontierResearchRecordResponse,
    AiFrontierResearchRecordWriteRequest,
    AiHotTrackerRunEvaluationResponse,
    AiHotTrackerTrackingStateResponse,
    AiHotTrackerTrackingRunCreateRequest,
    AiHotTrackerTrackingRunFollowUpRequest,
    AiHotTrackerTrackingRunFollowUpResponse,
    AiHotTrackerTrackingRunResponse,
)
from app.schemas.research_analysis_review import ResearchAnalysisReviewResponse
from app.schemas.research_analysis_run import ResearchAnalysisRunCreate, ResearchAnalysisRunResponse
from app.schemas.research_external_resource_snapshot import ResearchExternalResourceSnapshotResponse
from app.services.ai_frontier_research_record_service import (
    AiFrontierResearchRecordAccessError,
    delete_ai_frontier_research_record,
    get_ai_frontier_research_record,
    list_workspace_ai_frontier_research_records,
    save_ai_frontier_research_record,
    update_ai_frontier_research_record,
)
from app.services.ai_hot_tracker_tracking_service import (
    AiHotTrackerTrackingAccessError,
    answer_ai_hot_tracker_follow_up,
    create_ai_hot_tracker_tracking_run,
    delete_ai_hot_tracker_tracking_run,
    get_ai_hot_tracker_run_evaluation,
    get_ai_hot_tracker_tracking_run,
    get_ai_hot_tracker_tracking_state,
    list_workspace_ai_hot_tracker_tracking_runs,
)
from app.services.research_analysis_review_service import list_workspace_research_analysis_review
from app.services.research_analysis_run_service import (
    ResearchAnalysisRunAccessError,
    ResearchAnalysisRunExecutionError,
    ResearchAnalysisRunQueueError,
    ResearchAnalysisRunValidationError,
    create_research_analysis_run,
    get_research_analysis_run,
    list_workspace_research_analysis_runs,
)
from app.services.research_external_resource_snapshot_service import (
    ResearchExternalResourceSnapshotAccessError,
    ResearchExternalResourceSnapshotValidationError,
    list_workspace_research_external_resource_snapshots,
)
from app.services.retrieval_generation_service import ChatProcessingError

router = APIRouter()


@router.post(
    "/workspaces/{workspace_id}/ai-hot-tracker/report",
    response_model=AiHotTrackerTrackingRunResponse,
)
async def generate_hot_tracker_report_alias(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
) -> AiHotTrackerTrackingRunResponse:
    try:
        return create_ai_hot_tracker_tracking_run(
            workspace_id=workspace_id,
            user_id=current_user.id,
        )
    except AiHotTrackerTrackingAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post(
    "/workspaces/{workspace_id}/ai-hot-tracker/runs",
    response_model=AiHotTrackerTrackingRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_hot_tracker_run(
    workspace_id: str,
    payload: AiHotTrackerTrackingRunCreateRequest | None = None,
    current_user: User = Depends(get_current_user),
) -> AiHotTrackerTrackingRunResponse:
    try:
        return create_ai_hot_tracker_tracking_run(
            workspace_id=workspace_id,
            user_id=current_user.id,
            payload=payload,
        )
    except AiHotTrackerTrackingAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get(
    "/workspaces/{workspace_id}/ai-hot-tracker/runs",
    response_model=list[AiHotTrackerTrackingRunResponse],
)
async def list_hot_tracker_runs(
    workspace_id: str,
    limit: int = Query(default=12, ge=1, le=20),
    current_user: User = Depends(get_current_user),
) -> list[AiHotTrackerTrackingRunResponse]:
    try:
        return list_workspace_ai_hot_tracker_tracking_runs(
            workspace_id=workspace_id,
            user_id=current_user.id,
            limit=limit,
        )
    except AiHotTrackerTrackingAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get(
    "/workspaces/{workspace_id}/ai-hot-tracker/state",
    response_model=AiHotTrackerTrackingStateResponse,
)
async def get_hot_tracker_state(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
) -> AiHotTrackerTrackingStateResponse:
    try:
        return get_ai_hot_tracker_tracking_state(
            workspace_id=workspace_id,
            user_id=current_user.id,
        )
    except AiHotTrackerTrackingAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get(
    "/ai-hot-tracker/runs/{run_id}",
    response_model=AiHotTrackerTrackingRunResponse,
)
async def get_hot_tracker_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
) -> AiHotTrackerTrackingRunResponse:
    run = get_ai_hot_tracker_tracking_run(run_id=run_id, user_id=current_user.id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI hot tracker run not found")
    return run


@router.get(
    "/ai-hot-tracker/runs/{run_id}/evaluation",
    response_model=AiHotTrackerRunEvaluationResponse,
)
async def get_hot_tracker_run_evaluation(
    run_id: str,
    current_user: User = Depends(get_current_user),
) -> AiHotTrackerRunEvaluationResponse:
    try:
        return get_ai_hot_tracker_run_evaluation(
            run_id=run_id,
            user_id=current_user.id,
        )
    except AiHotTrackerTrackingAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.delete("/ai-hot-tracker/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hot_tracker_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
) -> None:
    deleted = delete_ai_hot_tracker_tracking_run(run_id=run_id, user_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI hot tracker run not found")


@router.post(
    "/ai-hot-tracker/runs/{run_id}/follow-up",
    response_model=AiHotTrackerTrackingRunFollowUpResponse,
)
async def follow_up_ai_hot_tracker_run(
    run_id: str,
    payload: AiHotTrackerTrackingRunFollowUpRequest,
    current_user: User = Depends(get_current_user),
) -> AiHotTrackerTrackingRunFollowUpResponse:
    try:
        return answer_ai_hot_tracker_follow_up(
            run_id=run_id,
            user_id=current_user.id,
            payload=payload,
        )
    except AiHotTrackerTrackingAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ChatProcessingError as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error


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


@router.get(
    "/workspaces/{workspace_id}/ai-frontier-records",
    response_model=list[AiFrontierResearchRecordResponse],
)
async def list_ai_frontier_records(
    workspace_id: str,
    limit: int = Query(default=8, ge=1, le=20),
    current_user: User = Depends(get_current_user),
) -> list[AiFrontierResearchRecordResponse]:
    try:
        return list_workspace_ai_frontier_research_records(
            workspace_id=workspace_id,
            user_id=current_user.id,
            limit=limit,
        )
    except AiFrontierResearchRecordAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post(
    "/workspaces/{workspace_id}/ai-frontier-records",
    response_model=AiFrontierResearchRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def save_ai_frontier_record(
    workspace_id: str,
    payload: AiFrontierResearchRecordWriteRequest,
    current_user: User = Depends(get_current_user),
) -> AiFrontierResearchRecordResponse:
    try:
        return save_ai_frontier_research_record(
            workspace_id=workspace_id,
            user_id=current_user.id,
            payload=payload,
        )
    except AiFrontierResearchRecordAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/ai-frontier-records/{record_id}", response_model=AiFrontierResearchRecordResponse)
async def get_ai_frontier_record(
    record_id: str,
    current_user: User = Depends(get_current_user),
) -> AiFrontierResearchRecordResponse:
    record = get_ai_frontier_research_record(record_id=record_id, user_id=current_user.id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI frontier research record not found")
    return record


@router.put("/ai-frontier-records/{record_id}", response_model=AiFrontierResearchRecordResponse)
async def update_ai_frontier_record(
    record_id: str,
    payload: AiFrontierResearchRecordWriteRequest,
    current_user: User = Depends(get_current_user),
) -> AiFrontierResearchRecordResponse:
    record = update_ai_frontier_research_record(
        record_id=record_id,
        user_id=current_user.id,
        payload=payload,
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI frontier research record not found")
    return record


@router.delete("/ai-frontier-records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_frontier_record(
    record_id: str,
    current_user: User = Depends(get_current_user),
) -> None:
    deleted = delete_ai_frontier_research_record(record_id=record_id, user_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI frontier research record not found")


@router.get("/research-analysis-runs/{run_id}", response_model=ResearchAnalysisRunResponse)
async def get_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
) -> ResearchAnalysisRunResponse:
    run = get_research_analysis_run(run_id=run_id, user_id=current_user.id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research analysis run not found")
    return run
