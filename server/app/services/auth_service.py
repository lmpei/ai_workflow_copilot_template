from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.repositories import user_repository
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, UserResponse
from app.services.public_demo_service import ensure_registration_allowed


class AuthConflictError(Exception):
    pass


class AuthCredentialsError(Exception):
    pass


def _to_user_response(user) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
    )


def register_user(payload: RegisterRequest) -> UserResponse:
    ensure_registration_allowed()
    existing_user = user_repository.get_user_by_email(payload.email)
    if existing_user is not None:
        raise AuthConflictError("该邮箱已被注册")

    password_hash = hash_password(payload.password)
    user = user_repository.create_user(
        email=payload.email,
        password_hash=password_hash,
        name=payload.name,
        role="owner",
    )
    return _to_user_response(user)


def login_user(payload: LoginRequest) -> LoginResponse:
    user = user_repository.get_user_by_email(payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise AuthCredentialsError("邮箱或密码不正确")

    access_token = create_access_token(user_id=user.id)
    return LoginResponse(
        access_token=access_token,
        user=_to_user_response(user),
    )


def get_current_user_response(user) -> UserResponse:
    return _to_user_response(user)
