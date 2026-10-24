import os
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

load_dotenv()


class PostgressDatabaseConnection:
    """
    Singleton class — shared PostgreSQL connection provider across the project.
    """

    _instance: Optional["PostgressDatabaseConnection"] = None
    _engine: Optional[AsyncEngine] = None
    _session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._engine is None:
            database_url = os.getenv("DATABASE_URL")

            if not database_url:
                raise ValueError("DATABASE_URL is not set in .env file")

            if database_url.startswith("postgresql://"):
                database_url = database_url.replace(
                    "postgresql://", "postgresql+asyncpg://", 1
                )
            elif database_url.startswith("postgres://"):
                database_url = database_url.replace(
                    "postgres://", "postgres+asyncpg://", 1
                )

            if "?" in database_url:
                database_url = database_url.split("?")[0]

            self._engine = create_async_engine(
                database_url,
                echo=False,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=180,
                connect_args={
                    "ssl": "require",
                    "statement_cache_size": 0,
                },
            )
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    async def get_session(self) -> AsyncSession:
        """
        Asynchronously creates and returns an AsyncSession instance.
        """
        return self._session_factory()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Async context manager wrapper. Auto-closes the session when exiting the block.
        """
        async_session = self._session_factory()
        try:
            yield async_session
        finally:
            await async_session.close()

    async def close(self):
        await self._engine.dispose()


db_connection = PostgressDatabaseConnection()