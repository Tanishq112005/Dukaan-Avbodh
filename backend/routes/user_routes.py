# routes/user_routes.py
from fastapi import APIRouter, Depends
from controllers.user_controller import UserController
from middleware.role_middleware import get_current_user

router = APIRouter(prefix="/user", tags=["User"])
controller = UserController()


from pydantic import BaseModel
from typing import Optional

class LogEventRequest(BaseModel):
    product_id: Optional[int] = None
    event_type: str
    category: str = "general"

async def get_profile_route(current_user: dict = Depends(get_current_user)):
    return await controller.get_profile(current_user["user_id"])

async def log_event_route(payload: LogEventRequest, current_user: dict = Depends(get_current_user)):
    return await controller.log_event(
        user_id=current_user["user_id"],
        product_id=payload.product_id,
        event_type=payload.event_type,
        category=payload.category
    )

router.add_api_route("/profile", get_profile_route, methods=["GET"])
router.add_api_route("/event", log_event_route, methods=["POST"])