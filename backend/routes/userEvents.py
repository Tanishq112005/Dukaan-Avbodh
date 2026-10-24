from fastapi import APIRouter, Depends, Query

from middleware.auth_middleware import auth_middleware
from schemas.userEvent import UserEvent
from controllers.userEvent import userEventController

router = APIRouter(
    prefix="/userEvents",
    tags=["User Events"]
)


# Add a user event
@router.post("/add", status_code=200)
async def add_user_event(
    payload: UserEvent,
    current_user: dict = Depends(auth_middleware)
):
    return await userEventController.addUserEvent(
        payload=payload,
        user_id=current_user["user_id"]
    )


# Get events of the authenticated user
@router.get("/get")
async def get_user_events(
    current_user: dict = Depends(auth_middleware)
):
    return await userEventController.getUserEvents(
        user_id=current_user["user_id"]
    )


# Get recent events across all users
@router.get("/allUserEvents")
async def get_all_user_events(
    limit: int = Query(default=10, ge=1, le=100),
    current_user: dict = Depends(auth_middleware)
):
    
    return await userEventController.getAllUserEvent(
        limit=limit
    )