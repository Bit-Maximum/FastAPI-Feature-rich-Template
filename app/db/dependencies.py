from collections.abc import AsyncGenerator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from taskiq import TaskiqDepends

from app.core import security
from app.core.config import settings
from app.db.models.jwt_token import TokenPayload
from app.db.models.users import User

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.API_BASE_PATH}/login/access-token")


async def get_db_session(
    request: Annotated[Request, TaskiqDepends()],
) -> AsyncGenerator[AsyncSession]:
    """
    Create and get database session.

    :param request: current request.
    :yield: database session.
    """
    session: AsyncSession = request.app.state.db_session_factory()

    try:
        yield session
    finally:
        await session.commit()
        await session.close()


SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


async def get_current_user(session: SessionDep, token: TokenDep) -> User:
    """
    Retrieve the currently authenticated user from the database based on the JWT token.

    Args:
        session: Database session dependency.
        token: JWT bearer token dependency.

    Returns:
        The User object corresponding to the token subject.

    Raises:
        HTTPException: If the token is invalid, user does not exist, or is inactive.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError) as err:
        # Raised if token is tampered, expired, or payload is malformed
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        ) from err

    user: User | None = await session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_active_superuser(current_user: CurrentUser) -> User:
    """
    Ensure that the current user has superuser privileges.

    Args:
        current_user: The currently authenticated user dependency.

    Returns:
        The current user if they are a superuser.

    Raises:
        HTTPException: If the user is not a superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user
