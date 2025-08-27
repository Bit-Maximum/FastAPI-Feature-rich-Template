from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


ALGORITHM = "HS256"


def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    """
    Generate a JWT access token for the given subject with an expiration delta.

    Args:
        subject: The user identifier (or any subject) to embed.
        expires_delta: Amount of time before the token expires.

    Returns:
        Encoded JWT as a string.
    """
    expire = datetime.now(UTC) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against its hashed version.

    Args:
        plain_password: The user-supplied raw password.
        hashed_password: The securely stored hashed password.

    Returns:
        True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generate a secure hash for the given password.

    Uses the application's configured password hashing context to securely
    transform plaintext passwords for safe storage or comparison.
    """
    return pwd_context.hash(password)
