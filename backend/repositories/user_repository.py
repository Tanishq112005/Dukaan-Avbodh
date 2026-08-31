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

    async def ensure_guest_exists(self, user_id: int) -> None:
        """
        Guest users (login nahi kiye hue) ke liye bhi ek User row ensure karta hai,
        taaki UserEvent/Cart jaise foreign-key wale tables mein unka data save ho
        sake. Frontend jo bhi ID (guestId) chat/product-view ke liye use kar raha
        hai, wahi yahan pass honi chahiye.
        """
        from models.user import UserRole
        async with db_connection.get_session() as session:
            try:
                result = await session.exec(select(User).where(User.id == user_id))
                if result.first():
                    return
                guest = User(
                    id=user_id,
                    name=f"Guest {user_id}",
                    role=UserRole.CUSTOMER,
                    identifier=f"guest_{user_id}@dukaan.local",
                )
                session.add(guest)
                await session.commit()
            except Exception:
                await session.rollback()
                # Race condition (do requests ek saath guest bana rahe) — safe to ignore
            finally:
                await session.close()