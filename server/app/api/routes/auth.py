from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
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
    login_user,
    register_user,
)

router = APIRouter()


@router.post("/auth/enter", response_model=LoginResponse)
async def enter(payload: AuthEntryRequest) -> LoginResponse:
    try:
        return enter_user(payload)
    except AuthCredentialsError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)) from error


@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest) -> UserResponse:
    try:
        return register_user(payload)
    except AuthConflictError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.post("/auth/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    try:
        return login_user(payload)
    except AuthCredentialsError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)) from error


@router.get("/auth/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return get_current_user_response(current_user)
