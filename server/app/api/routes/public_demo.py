from fastapi import APIRouter

from app.schemas.public_demo import PublicDemoSettingsResponse
from app.services.public_demo_service import get_public_demo_settings

router = APIRouter()


@router.get("/public-demo", response_model=PublicDemoSettingsResponse)
async def get_public_demo() -> PublicDemoSettingsResponse:
    return get_public_demo_settings()
