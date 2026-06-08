"""
Database connection helper for pipelines and notebooks.

Usage:
    from pipelines.common.db import get_engine, get_session

    engine = get_engine()  # reads DATABASE_URL or individual PG vars from env
    async with get_session(engine) as session:
        ...
"""

import os
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def build_database_url() -> str:
    """Build async database URL from env vars."""
    url = os.environ.get("DATABASE_URL")
    if url:
        # Ensure async driver
        return url.replace("postgresql://", "postgresql+asyncpg://")

    user = os.environ.get("POSTGRES_USER")
    password = os.environ.get("POSTGRES_PASSWORD")
    host = os.environ.get("POSTGRES_HOST")
    port = os.environ.get("POSTGRES_PORT")
    db = os.environ.get("POSTGRES_DB")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


def get_engine(echo: bool = False):
    return create_async_engine(build_database_url(), echo=echo)


def get_session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_session(engine=None):
    if engine is None:
        engine = get_engine()
    factory = get_session_factory(engine)
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
