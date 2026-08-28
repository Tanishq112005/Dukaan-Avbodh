# repositories/user_event_repository.py
from sqlmodel import select
from config.database import db_connection
from models import UserEvent
from .base_repository import BaseRepository


class UserEventRepository(BaseRepository[UserEvent]):
    def __init__(self):
        super().__init__(UserEvent)

    async def get_events_for_user(self, user_id: int) -> list[UserEvent]:
        async with db_connection.get_session() as session:
            try:
                result = await session.exec(
                    select(UserEvent).where(UserEvent.user_id == user_id)
                )
                return result.all()
            except Exception as e:
                raise e
            finally:
                await session.close()