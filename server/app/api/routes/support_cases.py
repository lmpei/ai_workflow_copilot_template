from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.support import SupportCaseResponse, SupportCaseSummaryResponse
from app.services import support_case_service
from app.services.support_case_service import SupportCaseAccessError

router = APIRouter()


@router.get(
    "/workspaces/{workspace_id}/support-cases",
    response_model=list[SupportCaseSummaryResponse],
)
async def list_support_cases(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
) -> list[SupportCaseSummaryResponse]:
    try:
        return support_case_service.list_workspace_support_cases(
            workspace_id=workspace_id,
            user_id=current_user.id,
        )
    except SupportCaseAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/support-cases/{case_id}", response_model=SupportCaseResponse)
async def get_support_case(
    case_id: str,
    current_user: User = Depends(get_current_user),
) -> SupportCaseResponse:
    case = support_case_service.get_support_case(
        case_id=case_id,
        user_id=current_user.id,
    )
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="\u672a\u627e\u5230 Support case",
        )
    return case
