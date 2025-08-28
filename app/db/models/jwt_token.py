from app.db.base import Base


class Token(Base):
    """
    Represents an access token response with its type.
    Used for transmitting access tokens to clients after authentication.
    """

    access_token: str
    token_type: str = "bearer"  # # noqa: S105


class TokenPayload(Base):
    """Represents the payload section of a JWT, commonly holding user identification (subject)."""

    sub: str | None = None
