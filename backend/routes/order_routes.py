from fastapi import APIRouter, Depends
from controllers.order_controller import OrderController
from middleware.role_middleware import require_role, get_current_user
from models.user import UserRole

router = APIRouter(prefix="/order", tags=["Order"])
controller = OrderController()


async def my_orders_route(current_user: dict = Depends(get_current_user)):
    return await controller.get_my_orders(current_user["user_id"])


async def all_orders_route(current_user: dict = Depends(require_role(UserRole.MERCHANT))):
    return await controller.get_all_orders()


async def update_status_route(
    order_id: int,
    status: str,
    current_user: dict = Depends(require_role(UserRole.MERCHANT))
):
    return await controller.update_status(order_id, status, current_user["user_id"])


router.add_api_route("/my-orders", my_orders_route, methods=["GET"])
router.add_api_route("/all", all_orders_route, methods=["GET"])
router.add_api_route("/{order_id}/status", update_status_route, methods=["PATCH"])