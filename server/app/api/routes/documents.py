from fastapi import APIRouter, HTTPException, status

from app.services.document_service import get_document_module_status

router = APIRouter()


@router.post(
    "/workspaces/{workspace_id}/documents/upload",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
)
async def upload_document(workspace_id: str) -> dict:
    detail = get_document_module_status()
    detail["workspace_id"] = workspace_id
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=detail)


@router.get("/workspaces/{workspace_id}/documents", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def list_documents(workspace_id: str) -> dict:
    detail = get_document_module_status()
    detail["workspace_id"] = workspace_id
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=detail)


@router.get("/documents/{document_id}", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def get_document(document_id: str) -> dict:
    detail = get_document_module_status()
    detail["document_id"] = document_id
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=detail)


@router.post("/documents/{document_id}/reindex", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def reindex_document(document_id: str) -> dict:
    detail = get_document_module_status()
    detail["document_id"] = document_id
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=detail)
