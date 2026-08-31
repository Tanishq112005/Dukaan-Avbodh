from repositories import UserRepository
from repositories.user_event_repository import UserEventRepository
from models.user_event import UserEvent, EventType
from fastapi import HTTPException

class UserController:
    def __init__(self):
        self.user_repo = UserRepository()
        self.event_repo = UserEventRepository()

    async def get_profile(self, user_id: int):
        return await self.user_repo.get_by_id(user_id)

    async def log_event(self, user_id: int, product_id: int, event_type: str, category: str = "general"):
        try:
            event = UserEvent(
                user_id=user_id,
                product_id=product_id,
                event_type=EventType(event_type),
                category=category
            )
            await self.event_repo.create(event)
            return {"success": True}
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid event type")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))