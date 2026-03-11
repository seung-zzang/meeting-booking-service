from typing import Annotated
import os

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
)


# DATABASE_URL 이 설정되어 있으면 (예: RDS PostgreSQL),
# 그 값을 사용하고, 없으면 로컬 SQLite 를 기본으로 사용합니다.
DSN = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./local.db")


def create_engine(dsn: str | None = None) -> AsyncEngine:
    if dsn is None:
        dsn = DSN

    return create_async_engine(
        dsn,
        echo=False,
    )


def create_session(async_engine: AsyncEngine | None = None):
    if async_engine is None:
        async_engine = create_engine()

    return async_sessionmaker(
        async_engine,
        expire_on_commit=False,
        autoflush=False,
        class_=AsyncSession,
    )


engine = create_engine()
async_session_factory = create_session(engine)


async def use_session():
    async with async_session_factory() as session:
        yield session


DbSessionDep = Annotated[AsyncSession, Depends(use_session)]