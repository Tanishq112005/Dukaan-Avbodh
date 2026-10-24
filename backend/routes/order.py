from fastapi import APIRouter, Depends
from controllers.order import orderController
from middleware import auth_middleware


router = APIRouter(prefix="/order", tags=["Order"])



async def create_order_route( current_user: dict = Depends(auth_middleware)):
    return await orderController.create_order(current_user["user_id"])


async def my_orders_route( current_user: dict = Depends(auth_middleware)):
    return await orderController.get_user_orders(current_user["user_id"])




router.add_api_route("/create", create_order_route, methods=["POST"])
router.add_api_route("/get", my_orders_route, methods=["GET"])
