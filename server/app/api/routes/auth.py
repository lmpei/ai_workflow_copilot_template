from fastapi import APIRouter, HTTPException, status

from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import preview_registered_user

router = APIRouter()


@router.post("/auth/register", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def register(payload: RegisterRequest) -> dict:
    user = preview_registered_user(payload)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "status": "scaffolded",
            "message": "Auth persistence and token issuance start in Phase 1 Platform MVP.",
            "preview_user": user.model_dump(mode="json"),
        },
    )


@router.post("/auth/login", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def login(payload: LoginRequest) -> dict:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "status": "scaffolded",
            "message": "Login is planned for Phase 1 after database and auth provider integration.",
            "email": payload.email,
        },
    )


@router.get("/auth/me", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def me() -> dict:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Current-user lookup is a Phase 1 scaffold and is not implemented yet.",
    )
