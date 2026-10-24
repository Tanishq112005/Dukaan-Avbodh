# repositories/user_event_repository.py
from sqlmodel import select
from config.database import db_connection
from models import UserEvent
from .base_repository import BaseRepository


class UserEvent(BaseRepository[UserEvent]):
    
    ## initilization of the class
    def __init__(self , db_connection):
        super().__init__(UserEvent)
        self.db = db_connection

    async def get_events_for_user(self, user_id: int) -> list[UserEvent]:
        async with self.db.get_session() as session:
            try:
                result = await session.exec(
                    select(UserEvent).where(UserEvent.user_id == user_id)
                )
                return result.all()
            except Exception as e:
                raise e
            finally:
                await session.close()

    async def get_recent_global_events(self, limit: int = 500) -> list[UserEvent]:
        async with self.db.get_session() as session:
            try:
                result = await session.exec(
                    select(UserEvent).order_by(UserEvent.timestamp.desc()).limit(limit)
                )
                return result.all()
            except Exception as e:
                raise e
            finally:
                await session.close()
                
                
userEvent = UserEvent(db_connection)                