import uuid
from sqlmodel import select
from config.database import db_connection
from models.user import User, UserRole

class A2AService:
    async def create_session(self) -> str:
        token = f"a2a_{uuid.uuid4().hex[:12]}"
        async with db_connection.get_session() as session:
            user = User(name=f"Guest_{token[-4:]}", role=UserRole.AI_AGENT, identifier=token)
            session.add(user)
            await session.commit()
        return token

    async def get_or_create_user(self, chat_token: str) -> int:
        async with db_connection.get_session() as session:
            user = (await session.exec(select(User).where(User.identifier == chat_token))).first()
            if not user:
                user = User(name=f"Agent {chat_token[-4:]}", role=UserRole.AI_AGENT, identifier=chat_token)
                session.add(user)
                await session.commit()
                await session.refresh(user)
            return user.id

a2a_service = A2AService()
