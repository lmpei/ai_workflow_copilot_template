from app.core.security import hash_password
from app.schemas.auth import RegisterRequest, UserResponse


def preview_registered_user(payload: RegisterRequest) -> UserResponse:
    password_hash = hash_password(payload.password)
    return UserResponse(
        id=f"user-{password_hash[:8]}",
        email=payload.email,
        name=payload.name,
        role="owner",
    )
