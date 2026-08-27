# routes/user_routes.py
from fastapi import APIRouter, Depends
from controllers.user_controller import UserController
from middleware.role_middleware import get_current_user

router = APIRouter(prefix="/user", tags=["User"])
controller = UserController()


async def get_profile_route(current_user: dict = Depends(get_current_user)):
    return await controller.get_profile(current_user["user_id"])


router.add_api_route("/profile", get_profile_route, methods=["GET"])