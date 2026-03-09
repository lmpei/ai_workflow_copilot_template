import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.repositories import user_repository

AUTH_TOKEN_URL = "/api/v1/auth/login"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=AUTH_TOKEN_URL, auto_error=False)
AUTH_SECRET_KEY = os.environ.get("AUTH_SECRET_KEY", "phase1-dev-secret")
ACCESS_TOKEN_EXPIRE_HOURS = 24


def _b64url_encode(raw_bytes: bytes) -> str:
    return base64.urlsafe_b64encode(raw_bytes).rstrip(b"=").decode("utf-8")


def _b64url_decode(encoded: str) -> bytes:
    padding = "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(f"{encoded}{padding}")


def _encode_token(payload: dict[str, str | int]) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_segment = _b64url_encode(
        json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    payload_segment = _b64url_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
    signature = hmac.new(
        AUTH_SECRET_KEY.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    signature_segment = _b64url_encode(signature)
    return f"{header_segment}.{payload_segment}.{signature_segment}"


def _decode_token(token: str) -> dict[str, str | int]:
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
    except ValueError as error:
        raise ValueError("Malformed token") from error

    signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
    expected_signature = hmac.new(
        AUTH_SECRET_KEY.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    actual_signature = _b64url_decode(signature_segment)
    if not hmac.compare_digest(actual_signature, expected_signature):
        raise ValueError("Invalid token signature")

    payload = json.loads(_b64url_decode(payload_segment))
    if not isinstance(payload, dict):
        raise ValueError("Invalid token payload")
    return payload


def create_access_token(*, user_id: str) -> str:
    expires_at = int((datetime.now(UTC) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)).timestamp())
    return _encode_token({"sub": user_id, "exp": expires_at})


def _unauthorized_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 100_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, encoded_value: str) -> bool:
    parts = encoded_value.split("$", 1)
    if len(parts) != 2:
        return False

    salt, expected = parts
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 100_000)
    return secrets.compare_digest(actual.hex(), expected)


def get_current_user_from_token(token: str):
    try:
        payload = _decode_token(token)
    except (ValueError, json.JSONDecodeError) as error:
        raise _unauthorized_exception() from error

    user_id = payload.get("sub")
    expires_at = payload.get("exp")
    if not isinstance(user_id, str) or not isinstance(expires_at, int):
        raise _unauthorized_exception()
    if expires_at < int(datetime.now(UTC).timestamp()):
        raise _unauthorized_exception()

    user = user_repository.get_user_by_id(user_id)
    if user is None:
        raise _unauthorized_exception()

    return user


def get_current_user(token: str | None = Depends(oauth2_scheme)):
    if token is None:
        raise _unauthorized_exception()
    return get_current_user_from_token(token)
