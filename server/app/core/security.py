import hashlib
import secrets

from fastapi.security import OAuth2PasswordBearer

AUTH_TOKEN_URL = "/api/v1/auth/login"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=AUTH_TOKEN_URL, auto_error=False)


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
