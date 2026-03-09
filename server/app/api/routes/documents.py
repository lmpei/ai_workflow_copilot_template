from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.services.document_service import (
    DocumentAccessError,
    DocumentUploadError,
    get_document,
    list_documents,
    reindex_document,
    upload_document,
)

router = APIRouter()


@router.post(
    "/workspaces/{workspace_id}/documents/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_workspace_document(
    workspace_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    try:
        return await upload_document(
            workspace_id=workspace_id,
            user_id=current_user.id,
            file=file,
        )
    except DocumentAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except DocumentUploadError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/workspaces/{workspace_id}/documents", response_model=list[DocumentResponse])
async def list_workspace_documents(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
) -> list[DocumentResponse]:
    try:
        return list_documents(workspace_id=workspace_id, user_id=current_user.id)
    except DocumentAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_workspace_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    document = get_document(document_id=document_id, user_id=current_user.id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.post("/documents/{document_id}/reindex", response_model=DocumentResponse)
async def reindex_workspace_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    document = reindex_document(document_id=document_id, user_id=current_user.id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document
