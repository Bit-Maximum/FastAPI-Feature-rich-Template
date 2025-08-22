from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings


async def create_database() -> None:
    """Create a database."""
    db_url = make_url(str(settings.db_url.with_path("/postgres")))
    engine = create_async_engine(
        db_url,
        isolation_level="AUTOCOMMIT",
        echo=settings.DB_ECHO,
        pool_size=settings.CONNECTION_POOL_SIZE,
        max_overflow=settings.CONNECTION_MAX_OVERFLOW,
        pool_timeout=settings.CONNECTION_POOL_TIMEOUT,
        pool_recycle=settings.CONNECTION_POOL_RECYCLE,
        pool_pre_ping=True,
    )

    async with engine.connect() as conn:
        database_existance = await conn.execute(
            text(
                f"SELECT 1 FROM pg_database WHERE datname='{settings.DB_NAME}'",  # noqa: S608
            ),
        )
        database_exists = database_existance.scalar() == 1

    if database_exists:
        await drop_database()

    async with engine.connect() as conn:
        await conn.execute(
            text(
                f'CREATE DATABASE "{settings.DB_NAME}" ENCODING "utf8" TEMPLATE template1',
            ),
        )


async def drop_database() -> None:
    """Drop current database."""
    db_url = make_url(str(settings.db_url.with_path("/postgres")))
    engine = create_async_engine(db_url, isolation_level="AUTOCOMMIT")
    async with engine.connect() as conn:
        disc_users = (
            "SELECT pg_terminate_backend(pg_stat_activity.pid) "  # noqa: S608
            "FROM pg_stat_activity "
            f"WHERE pg_stat_activity.datname = '{settings.DB_NAME}' "
            "AND pid <> pg_backend_pid();"
        )
        await conn.execute(text(disc_users))
        await conn.execute(text(f'DROP DATABASE "{settings.DB_NAME}"'))
