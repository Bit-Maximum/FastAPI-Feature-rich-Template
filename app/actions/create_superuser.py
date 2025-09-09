import asyncio
import contextlib

from fastapi_users.exceptions import UserAlreadyExists
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.models.users import User, UserCreate, UserManager, get_user_db, get_user_manager


async def get_db_session() -> AsyncSession:
    """
    Asynchronously yield a SQLAlchemy async session.

    Yields:
        AsyncSession: SQLAlchemy asynchronous session object.
    """
    engine = create_async_engine(
        str(settings.db_url),
        echo=settings.DB_ECHO,
        echo_pool=settings.DB_ECHO_POOL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
    )
    session_factory = async_sessionmaker(
        engine,
        # See https://fastapi-users.github.io/fastapi-users/latest/configuration/databases/sqlalchemy/#asynchronous-driver
        expire_on_commit=False,
        autoflush=False,
    )
    session = session_factory()
    try:
        yield session
    finally:
        await session.commit()
        await session.close()


get_async_session_context = contextlib.asynccontextmanager(get_db_session)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


async def create_user(
    user_manager: UserManager,
    user_create: UserCreate,
) -> User:
    """
    Create a new user using the provided UserManager.

    Args:
        user_manager (UserManager): Instance for user management actions.
        user_create (UserCreate): New user creation parameters.

    Returns:
        User: The created user object.
    """
    return await user_manager.create(
        user_create=user_create,
        safe=False,
    )


async def create_superuser(
    email: EmailStr = settings.DEFAULT_EMAIL,
    password: str = settings.DEFAULT_PASSWORD,
    is_active: bool = settings.DEFAULT_IS_ACTIVE,
    is_superuser: bool = settings.DEFAULT_IS_SUPERUSER,
    is_verified: bool = settings.DEFAULT_IS_VERIFIED,
) -> User:
    """
    Create a superuser with given attributes, or raises if user exists.

    Args:
        email (EmailStr): Email for the superuser.
        password (str): Password for the superuser.
        is_active (bool): User is active flag.
        is_superuser (bool): User is superuser flag.
        is_verified (bool): User is verified flag.

    Returns:
        User: The created superuser.

    Raises:
        UserAlreadyExists: If a user with the given email already exists.
    """
    user_create = UserCreate(
        email=email,
        password=password,
        is_active=is_active,
        is_superuser=is_superuser,
        is_verified=is_verified,
    )

    try:
        # Context managers provide resources needed for user creation.
        async with (
            get_async_session_context() as session,
            get_user_db_context(session) as user_db,
            get_user_manager_context(user_db) as user_manager,
        ):
            user = await create_user(
                user_manager=user_manager,
                user_create=user_create,
            )
            print(f"User created {user}")  # noqa: T201
            return user
    except UserAlreadyExists:
        print(f"User {email} already exists")  # noqa: T201
        raise


if __name__ == "__main__":
    asyncio.run(create_superuser())
