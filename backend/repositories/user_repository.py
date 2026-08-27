# repositories/user_repository.py
from typing import Optional
from sqlmodel import select
from config.database import db_connection
from models import User
from .base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    async def get_by_identifier(self, identifier: str) -> Optional[User]:
        async with db_connection.get_session() as session:
            try:
                result = await session.exec(
                    select(User).where(User.identifier == identifier)
                )
                return result.first()
            except Exception as e:
                raise e
            finally:
                await session.close()

    async def get_or_create(
        self,
        name: str,
        role: str,
        identifier: str,
        address: Optional[str] = None
    ) -> User:
        existing = await self.get_by_identifier(identifier)
        if existing:
            return existing
        new_user = User(
            name=name,
            role=role,
            identifier=identifier,
            address=address
        )
        return await self.create(new_user)

    async def update_address(self, user_id: int, address: str) -> Optional[User]:
        async with db_connection.get_session() as session:
            try:
                result = await session.exec(
                    select(User).where(User.id == user_id)
                )
                user = result.first()
                if user:
                    user.address = address
                    session.add(user)
                    await session.commit()
                    await session.refresh(user)
                return user
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()