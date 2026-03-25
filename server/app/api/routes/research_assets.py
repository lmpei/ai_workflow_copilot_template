from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.research_asset import (
    ResearchAssetComparisonRequest,
    ResearchAssetComparisonResponse,
    ResearchAssetCreate,
    ResearchAssetResponse,
    ResearchAssetSummaryResponse,
)
from app.services import research_asset_service
from app.services.research_asset_service import (
    ResearchAssetAccessError,
    ResearchAssetValidationError,
)

router = APIRouter()


@router.post(
    "/workspaces/{workspace_id}/research-assets",
    response_model=ResearchAssetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_research_asset(
    workspace_id: str,
    payload: ResearchAssetCreate,
    current_user: User = Depends(get_current_user),
) -> ResearchAssetResponse:
    try:
        return research_asset_service.create_research_asset_from_task(
            workspace_id=workspace_id,
            user_id=current_user.id,
            payload=payload,
        )
    except ResearchAssetAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ResearchAssetValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get(
    "/workspaces/{workspace_id}/research-assets",
    response_model=list[ResearchAssetSummaryResponse],
)
async def list_research_assets(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
) -> list[ResearchAssetSummaryResponse]:
    try:
        return research_asset_service.list_workspace_research_assets(
            workspace_id=workspace_id,
            user_id=current_user.id,
        )
    except ResearchAssetAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/research-assets/{asset_id}", response_model=ResearchAssetResponse)
async def get_research_asset(
    asset_id: str,
    current_user: User = Depends(get_current_user),
) -> ResearchAssetResponse:
    asset = research_asset_service.get_research_asset(
        asset_id=asset_id,
        user_id=current_user.id,
    )
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research asset not found")
    return asset


@router.post("/research-assets/compare", response_model=ResearchAssetComparisonResponse)
async def compare_research_assets(
    payload: ResearchAssetComparisonRequest,
    current_user: User = Depends(get_current_user),
) -> ResearchAssetComparisonResponse:
    try:
        return research_asset_service.compare_research_assets(
            user_id=current_user.id,
            payload=payload,
        )
    except ResearchAssetAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ResearchAssetValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
