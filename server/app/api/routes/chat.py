from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.retrieval_service import (
    ChatAccessError,
    ChatProcessingError,
    process_chat_request,
)

router = APIRouter()


@router.post("/workspaces/{workspace_id}/chat", response_model=ChatResponse)
async def chat(
    workspace_id: str,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    try:
        return process_chat_request(
            workspace_id=workspace_id,
            user_id=current_user.id,
            payload=payload,
        )
    except ChatAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ChatProcessingError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error
