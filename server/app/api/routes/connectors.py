from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.connector import ConnectorConsentGrantRequest, WorkspaceConnectorStatusResponse
from app.services.connector_service import (
    ConnectorAccessError,
    ConnectorValidationError,
    get_workspace_connector_status,
    grant_workspace_connector_consent,
    list_workspace_connector_statuses,
)

router = APIRouter()


@router.get(
    "/workspaces/{workspace_id}/connectors",
    response_model=list[WorkspaceConnectorStatusResponse],
)
async def list_workspace_connectors(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
) -> list[WorkspaceConnectorStatusResponse]:
    try:
        return list_workspace_connector_statuses(
            workspace_id=workspace_id,
            user_id=current_user.id,
        )
    except ConnectorAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ConnectorValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get(
    "/workspaces/{workspace_id}/connectors/{connector_id}",
    response_model=WorkspaceConnectorStatusResponse,
)
async def get_workspace_connector(
    workspace_id: str,
    connector_id: str,
    current_user: User = Depends(get_current_user),
) -> WorkspaceConnectorStatusResponse:
    try:
        return get_workspace_connector_status(
            workspace_id=workspace_id,
            user_id=current_user.id,
            connector_id=connector_id,
        )
    except ConnectorAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ConnectorValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post(
    "/workspaces/{workspace_id}/connectors/{connector_id}/consent",
    response_model=WorkspaceConnectorStatusResponse,
    status_code=status.HTTP_201_CREATED,
)
async def grant_connector_consent(
    workspace_id: str,
    connector_id: str,
    payload: ConnectorConsentGrantRequest,
    current_user: User = Depends(get_current_user),
) -> WorkspaceConnectorStatusResponse:
    try:
        return grant_workspace_connector_consent(
            workspace_id=workspace_id,
            user_id=current_user.id,
            connector_id=connector_id,
            payload=payload,
        )
    except ConnectorAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ConnectorValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
