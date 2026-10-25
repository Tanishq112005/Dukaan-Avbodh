import os
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
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

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Async context manager wrapper. Auto-closes the session when exiting the block.
        Usage:
            async with db_connection.get_session() as session:
                ...
        """
        async_session = self._session_factory()
        try:
            yield async_session
        finally:
            await async_session.close()

    # Alias so both .session() and .get_session() work identically as async context managers
    session = get_session

    async def init_db(self):
        """
        Creates all SQLModel tables in PostgreSQL if they do not exist.
        Preserves existing data in tables like 'product'.
        """
        from sqlmodel import SQLModel
        # Ensure all models are registered with SQLModel.metadata
        import Product.models
        import User.models
        import Cart.models
        import Order.models
        import UserEvents.models
        import Recommedation.models

        async with self._engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    async def reset_tables_except_product(self) -> dict:
        """
        Drops all relational tables EXCEPT 'product' to allow schema updates,
        and then recreates fresh tables matching current model definitions.
        """
        from sqlalchemy import text
        from sqlmodel import SQLModel
        import Product.models
        import User.models
        import Cart.models
        import Order.models
        import UserEvents.models
        import Recommedation.models

        # Drop previous tables with CASCADE, strictly preserving 'product'
        tables_to_drop = [
            "cartitem",
            "cart",
            "order",
            "userevent",
            "probabilityofshowingitems",
            "probabilityofshowingitemsforparticularuser",
            "campaignproductlink",
            "campaign",
            "discountpolicy",
            "user",
        ]

        async with self._engine.begin() as conn:
            for table in tables_to_drop:
                await conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE;'))

            # Recreate all fresh tables according to current model definitions
            await conn.run_sync(SQLModel.metadata.create_all)

            # Check and verify product table count
            product_count_res = await conn.execute(text("SELECT COUNT(*) FROM product;"))
            product_count = product_count_res.scalar() or 0

            # List active tables
            res = await conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;")
            )
            tables = [r[0] for r in res.fetchall()]

        return {
            "dropped_tables": tables_to_drop,
            "current_tables": tables,
            "preserved_product_count": product_count,
        }

    async def close(self):
        await self._engine.dispose()


db_connection = PostgressDatabaseConnection()

# Ensure all SQLModel models are registered in the global SQLAlchemy registry
import Product.models  # noqa: F401
import User.models  # noqa: F401
import Cart.models  # noqa: F401
import Order.models  # noqa: F401
import UserEvents.models  # noqa: F401
import Recommedation.models  # noqa: F401

