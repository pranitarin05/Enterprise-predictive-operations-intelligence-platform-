"""
Security utilities: password hashing and JWT creation/verification.

This is the ONLY file in the app that should ever touch bcrypt or jose
directly -- every other file asks THIS module to hash/verify/encode/decode,
so if we ever need to change hashing algorithms or token structure,
there's exactly one place to change it.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config.settings import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(plain_password: str) -> str:
    """One-way hash. There is no function to reverse this."""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Hashes the input again and compares -- never decrypts the stored hash."""
    return _pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, tenant_id: str, role: str) -> str:
    """
    Short-lived token (15 min) sent with every API request.
    Payload is signed, not encrypted -- anyone can read it, only we can forge it.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "role": role,
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: str) -> str:
    """Longer-lived token (7 days) used only to obtain a new access token."""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": user_id, "type": "refresh", "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any] | None:
    """Returns the payload if the token is valid and unexpired, else None."""
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
