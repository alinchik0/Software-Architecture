# shared/security.py
import uuid
from datetime import UTC, datetime, timedelta
from argon2 import PasswordHasher
from jose import JWTError, jwt
from .config import get_settings

_hasher = PasswordHasher()

def hash_password(password: str) -> str:
    return _hasher.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except Exception:
        return False

def create_token(subject: str, token_type: str, ttl_seconds: int) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "typ": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl_seconds)).timestamp()),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])

def try_decode_token(token: str) -> dict | None:
    try:
        return decode_token(token)
    except JWTError:
        return None
