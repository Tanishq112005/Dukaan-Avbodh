import uuid
from sqlmodel import select
from config.database import db_connection
from models.user import User, UserRole

class A2AService:
    async def create_session(self) -> str:
        token = f"a2a_{uuid.uuid4().hex[:12]}"
        email = f"{token}@dukaan.local"
        async with db_connection.get_session() as session:
            user = User(name=f"Guest_{token[-4:]}", role=UserRole.CUSTOMER, email=email)
            session.add(user)
            await session.commit()
        return token

    async def get_or_create_user(self, chat_token: str) -> int:
        email = f"{chat_token}@dukaan.local"
        async with db_connection.get_session() as session:
            user = (await session.exec(select(User).where(User.email == email))).first()
            if not user:
                user = User(name=f"Agent {chat_token[-4:]}", role=UserRole.CUSTOMER, email=email)
                session.add(user)
                await session.commit()
                await session.refresh(user)
            return user.id

a2a_service = A2AService()
