from typing import List
from sqlmodel import select
from config.database import db_connection
from UserEvents.models import UserEvent, EventType


class UserEventRepository:
    
    ## Initialization of the repo
    def __init__(self, db_connection=None):
        from config.database import db_connection as default_db
        self.db = db_connection or default_db

    async def getEventsOfUser(self, user_id: int) -> list[UserEvent]:
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

    async def getRecentEventsOfUser(self, limit: int = 500) -> list[UserEvent]:
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

    async def addUserEvents(
        self,
        user_id: int,
        event_type: EventType,
        product_id: int,
        category: str = "general",
    ) -> UserEvent:
        async with self.db.get_session() as session:
            try:
                event = UserEvent(
                    user_id=user_id,
                    event_type=event_type,
                    product_id=product_id,
                    category=category or "general",
                )
                session.add(event)
                await session.commit()
                await session.refresh(event)
                return event
            except Exception:
                await session.rollback()
                raise

    get_events_for_user = getEventsOfUser
    get_recent_global_events = getRecentEventsOfUser

    async def bulkAddUserEvents(self, events: List[UserEvent]) -> List[UserEvent]:
        """Bulk inserts events into the database in a single database transaction."""
        if not events:
            return []
        async with self.db.get_session() as session:
            try:
                session.add_all(events)
                await session.commit()
                return events
            except Exception:
                await session.rollback()
                raise


userEvent = UserEventRepository(db_connection)
userEvents = userEvent
user_event_repository = userEvent
userEvent_db = userEvent
