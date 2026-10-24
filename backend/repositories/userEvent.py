# repositories/user_event_repository.py
from sqlmodel import select
from config.database import db_connection
from models import UserEvent , EventType

class UserEvent:
    
    ## initilization of the class
    def __init__(self , db_connection):
        self.db = db_connection

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
       self, user_id: int, event_type: EventType, product_id: int):
      async with self.db.get_session() as session:
        try:
            event = UserEvent(
                user_id=user_id,
                event_type=event_type,
                product_id=product_id
            )

            session.add(event)
            await session.commit()
            await session.refresh(event)

            return event

        except Exception:
            await session.rollback()
            raise
    
              
                
userEvent = UserEvent(db_connection)                