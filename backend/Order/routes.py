from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from Order.controller import orderController
from Order.schemas import CheckoutRequest
from middleware.auth_middleware import auth_middleware


router = APIRouter(prefix="/order", tags=["Order"])


async def create_order_route(current_user: dict = Depends(auth_middleware)):
    return await orderController.create_order(current_user["user_id"])


async def checkout_route(
    payload: Optional[CheckoutRequest] = None,
    current_user: dict = Depends(auth_middleware),
):
    return await orderController.checkout(current_user["user_id"], payload)


async def my_orders_route(current_user: dict = Depends(auth_middleware)):
    return await orderController.get_user_orders(current_user["user_id"])


async def get_order_by_id_route(
    order_id: int,
    current_user: dict = Depends(auth_middleware),
):
    order = await orderController.get_order_by_id(order_id, user_id=current_user["user_id"])
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return {"success": True, "order": orderController.format_order_summary(order)}


async def track_order_route(
    order_id: Optional[int] = None,
    current_user: dict = Depends(auth_middleware),
):
    return await orderController.get_order_tracking(order_id=order_id, user_id=current_user["user_id"])


async def cancel_order_route(
    order_id: int,
    current_user: dict = Depends(auth_middleware),
):
    return await orderController.cancel_order(order_id)


router.add_api_route("/create", create_order_route, methods=["POST"])
router.add_api_route("/checkout", checkout_route, methods=["POST"])
router.add_api_route("/get", my_orders_route, methods=["GET"])
router.add_api_route("/track", track_order_route, methods=["GET"])
router.add_api_route("/track/{order_id}", track_order_route, methods=["GET"])
router.add_api_route("/{order_id}", get_order_by_id_route, methods=["GET"])
router.add_api_route("/cancel/{order_id}", cancel_order_route, methods=["POST"])
