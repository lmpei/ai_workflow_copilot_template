from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.public_demo import (
    PublicDemoSettingsResponse,
    PublicDemoTemplateResponse,
    PublicDemoWorkspaceSeedResponse,
)
from app.services.indexing_service import DocumentIndexingError
from app.services.public_demo_service import PublicDemoLimitError, get_public_demo_settings
from app.services.public_demo_showcase_service import (
    create_public_demo_workspace,
    list_public_demo_templates,
)

router = APIRouter()


@router.get("/public-demo", response_model=PublicDemoSettingsResponse)
async def get_public_demo() -> PublicDemoSettingsResponse:
    return get_public_demo_settings()


@router.get("/public-demo/templates", response_model=list[PublicDemoTemplateResponse])
async def get_public_demo_templates() -> list[PublicDemoTemplateResponse]:
    return list_public_demo_templates()


@router.post(
    "/public-demo/templates/{template_id}/workspaces",
    response_model=PublicDemoWorkspaceSeedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_public_demo_template_workspace(
    template_id: str,
    current_user: User = Depends(get_current_user),
) -> PublicDemoWorkspaceSeedResponse:
    try:
        return create_public_demo_workspace(template_id=template_id, user_id=current_user.id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except PublicDemoLimitError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except DocumentIndexingError as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error
