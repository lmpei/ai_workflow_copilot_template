from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import get_settings
from app.core.security import (
    get_current_user,
    raise_if_password_auth_disabled,
    raise_if_public_auth_disabled,
)
from app.models.user import User
from app.schemas.auth import (
    AuthEntryRequest,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UserResponse,
)
from app.services.auth_service import (
    AuthConflictError,
    AuthCredentialsError,
    enter_user,
    get_current_user_response,
    issue_guest_session,
    login_user,
    register_user,
)

router = APIRouter()


@router.post("/auth/enter", response_model=LoginResponse)
async def enter(payload: AuthEntryRequest) -> LoginResponse:
    raise_if_password_auth_disabled()
    try:
        return enter_user(payload)
    except AuthCredentialsError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)) from error


@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest) -> UserResponse:
    raise_if_password_auth_disabled()
    try:
        return register_user(payload)
    except AuthConflictError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.post("/auth/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    raise_if_password_auth_disabled()
    try:
        return login_user(payload)
    except AuthCredentialsError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)) from error


@router.post("/auth/guest", response_model=LoginResponse)
async def guest() -> LoginResponse:
    raise_if_public_auth_disabled()
    if not get_settings().guest_access_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="访客体验暂未开放")

    try:
        return issue_guest_session()
    except AuthConflictError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.get("/auth/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return get_current_user_response(current_user)
