from typing import Optional
from sqlmodel import select
from config.database import db_connection
from models import User
from models.user import UserRole


class User:
    ### initilization of the repo or the class 
    def __init__(self , db_connection):
        self.db = db_connection
    
     
     ### get user by identifier (email or AI agent ID)
    async def get_by_identifier(self, identifier: str) -> Optional[User]:
        async with self.db.get_session() as session:
            result = await session.exec(
                select(User).where(User.identifier == identifier)
            )
            return result.first()
     
     ### get user by id
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


    ### update user profile
    async def update_profile(
        self,
        user_id: int,
        name: Optional[str] = None,
        email: Optional[str] = None,
        address: Optional[str] = None,
    ) -> Optional[User]:
        async with self.db.get_session() as session:
            try:
                result = await session.exec(select(User).where(User.id == user_id))
                user = result.first()
                if not user:
                    return None
                if name:
                    user.name = name
                if email:
                    user.identifier = email
                if address:
                    user.address = address
                session.add(user)
                await session.commit()
                await session.refresh(user)
                return user
            except Exception as e:
                await session.rollback()
                raise e
   
   
    ### update user address
    async def update_address(self, user_id: int, address: str) -> Optional[User]:
        async with self.db.get_session() as session:
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


    ### ensure guest user exists
    async def ensure_guest_exists(self, user_id: int) -> Optional[User]:
        
        async with self.db.get_session() as session:
            try:
                result = await session.exec(select(User).where(User.id == user_id))
                user = result.first()
                if user:
                    return user
                guest = User(
                    id=user_id,
                    name=f"Guest {user_id}",
                    role=UserRole.CUSTOMER,
                    identifier=f"guest_{user_id}@dukaan.local",
                )
                session.add(guest)
                await session.commit()
                await session.refresh(guest)
                return guest
            except Exception:
                await session.rollback()
                return None
            
            
            
### User          
userRepository = User(db_connection=db_connection)