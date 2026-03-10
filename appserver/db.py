import os
from typing import Annotated
from fastapi import Depends

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine
)


def normalize_dsn(dsn: str) -> str:
    dsn = dsn.strip()

    # Common shorthand used by some providers / examples
    if dsn.startswith("postgres://"):
        dsn = "postgresql://" + dsn[len("postgres://"):]

    # Ensure async-capable driver for create_async_engine
    if dsn.startswith("postgresql://") and "+psycopg" not in dsn and "+asyncpg" not in dsn:
        dsn = dsn.replace("postgresql://", "postgresql+psycopg://", 1)

    return dsn


def get_dsn() -> str:
    return normalize_dsn(os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./local.db"))


def create_engine(dsn: str):
    return create_async_engine(
        normalize_dsn(dsn),
        echo=os.getenv("SQL_ECHO", "false").lower() in {"1", "true", "yes", "on"},
    )

def create_session(async_engine: AsyncEngine | None = None):
    if async_engine is None:
        async_engine = create_engine(get_dsn())

    return async_sessionmaker(
        async_engine,
        expire_on_commit=False,
        autoflush=False,
        class_=AsyncSession,
    )


async def use_session():
    async with async_session_factory() as session:
        yield session
        

DbSessionDep = Annotated[AsyncSession, Depends(use_session)]



DSN = get_dsn()

engine = create_engine(DSN)

async_session_factory = create_session(engine)

