from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.job import JobHiringPacketResponse, JobHiringPacketSummaryResponse
from app.services import job_hiring_packet_service
from app.services.job_hiring_packet_service import JobHiringPacketAccessError

router = APIRouter()


@router.get(
    "/workspaces/{workspace_id}/job-hiring-packets",
    response_model=list[JobHiringPacketSummaryResponse],
)
async def list_job_hiring_packets(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
) -> list[JobHiringPacketSummaryResponse]:
    try:
        return job_hiring_packet_service.list_workspace_job_hiring_packets(
            workspace_id=workspace_id,
            user_id=current_user.id,
        )
    except JobHiringPacketAccessError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/job-hiring-packets/{packet_id}", response_model=JobHiringPacketResponse)
async def get_job_hiring_packet(
    packet_id: str,
    current_user: User = Depends(get_current_user),
) -> JobHiringPacketResponse:
    packet = job_hiring_packet_service.get_job_hiring_packet(
        packet_id=packet_id,
        user_id=current_user.id,
    )
    if packet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="\u672a\u627e\u5230 Job hiring packet",
        )
    return packet
