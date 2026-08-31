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

            # Remove unsupported query parameters like sslmode ya channel_binding
            # (asyncpg inhe URL mein samajhta nahi, connect() call fail ho jaata hai).
            # SSL yahan URL se nahi, connect_args se explicitly bhejte hain — warna
            # SSL bilkul off ho jaata hai aur Neon jaise providers connection reset
            # kar dete hain (WinError 10054 / "forcibly closed by remote host").
            if "?" in database_url:
                database_url = database_url.split("?")[0]

            self._engine = create_async_engine(
                database_url,
                echo=False,
                pool_size=5,          # kitne connections pool mein rakhne hain
                max_overflow=10,      # extra connections agar zaroorat pade
                pool_pre_ping=True,   # dead connections ko auto-detect karega
                connect_args={
                    "ssl": "require",
                    "statement_cache_size": 0,  # Neon pooler (PgBouncer, transaction mode) ke saath
                                                 # asyncpg ke prepared statements conflict karte hain —
                                                 # isse disable karna zaroori hai jab pooler use ho.
                },
            )
            self._session_factory = sessionmaker(
                self._engine, class_=AsyncSession, expire_on_commit=False
            )

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    def get_session(self) -> AsyncSession:
        return self._session_factory()

    async def init_db(self, retries: int = 3, delay_seconds: float = 2.0):
        """Saari models ke tables create karta hai (agar exist nahi karti).

        Neon (aur similar serverless Postgres) free-tier compute idle hone par
        auto-suspend ho jaata hai — pehla connection attempt use "wake up" karta
        hai aur usi waqt kabhi-kabhi connection reset ho jaata hai. Isliye chhota
        retry-with-backoff, taaki cold-start ki wajah se startup crash na ho.
        """
        from models import User, Product, Order, DiscountPolicy, UserEvent, Cart, CartItem
        import asyncio

        last_error = None
        for attempt in range(1, retries + 1):
            try:
                async with self._engine.begin() as conn:
                    await conn.run_sync(SQLModel.metadata.create_all)
                return
            except Exception as e:
                last_error = e
                if attempt < retries:
                    print(f"[DB] init_db attempt {attempt}/{retries} failed ({e.__class__.__name__}), retrying in {delay_seconds}s... (Neon compute cold-start ho sakta hai)")
                    await asyncio.sleep(delay_seconds)
        raise last_error

    async def close(self):
        await self._engine.dispose()


db_connection = DatabaseConnection()