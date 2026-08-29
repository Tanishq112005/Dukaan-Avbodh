# config/database.py
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()


class DatabaseConnection:
    """
    Singleton class — poore project (mcp, merchant dashboard, user app) ke liye
    ek hi shared PostgreSQL connection provide karti hai.
    """
    _instance: Optional["DatabaseConnection"] = None
    _engine: Optional[AsyncEngine] = None
    _session_factory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._engine is None:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                raise ValueError("DATABASE_URL .env file mein set nahi hai")
            
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)

            # Remove unsupported query parameters like sslmode or channel_binding
            if "?" in database_url:
                database_url = database_url.split("?")[0]

            self._engine = create_async_engine(
                database_url,
                echo=False,
                pool_size=5,          # kitne connections pool mein rakhne hain
                max_overflow=10,      # extra connections agar zaroorat pade
                pool_pre_ping=True    # dead connections ko auto-detect karega
            )
            self._session_factory = sessionmaker(
                self._engine, class_=AsyncSession, expire_on_commit=False
            )

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    def get_session(self) -> AsyncSession:
        return self._session_factory()

    async def init_db(self):
        """Saari models ke tables create karta hai (agar exist nahi karti)."""
        from models import User, Product, Order, DiscountPolicy , UserEvent

        async with self._engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    async def close(self):
        await self._engine.dispose()


db_connection = DatabaseConnection()