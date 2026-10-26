import logging
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status

from Order.database import OrderRepository, orderRepository, InsufficientStockError
from Payment.controller import paymentController
from Order.schemas import CheckoutRequest

logger = logging.getLogger(__name__)


class OrderController:
    def __init__(self, order_repo: Optional[OrderRepository] = None):
        self.order_repo = order_repo or orderRepository

    async def create_order(self, user_id: int):
        """Creates order for a user from their cart with stock reservation under lock."""
        try:
            order = await self.order_repo.createOrder(user_id=user_id)
            return {
                "success": True,
                "message": "Order created successfully with reserved stock",
                "order": order,
            }
        except InsufficientStockError as stock_err:
            logger.warning("Stock reservation failed for user %s: %s", user_id, stock_err)
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(stock_err))
        except ValueError as e:
            logger.warning("Validation error while creating order for user %s: %s", user_id, str(e))
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except HTTPException:
            raise
        except Exception:
            logger.exception("Failed to create order for user %s", user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create order",
            )

    async def checkout(self, user_id: int, req: Optional[CheckoutRequest] = None):
        """
        Unified checkout with concurrency lock and payment order generation:
        1. Checks stock and reserves inventory under multi-product locks.
        2. Generates Razorpay payment order.
        3. Returns order IDs and payment parameters for frontend checkout.
        """
        try:
            items_payload = None
            discount_pct = 0.0
            provider = "razorpay"
            currency = "INR"
            cust_name = None
            cust_email = None

            if req:
                if req.items:
                    items_payload = [it.dict() for it in req.items]
                discount_pct = req.discount_percentage or 0.0
                provider = req.provider or "razorpay"
                currency = req.currency or "INR"
                cust_name = req.customer_name
                cust_email = req.customer_email

            return await paymentController.checkout_with_concurrency_lock(
                user_id=user_id,
                items=items_payload,
                discount_percentage=discount_pct,
                provider=provider,
                currency=currency,
                customer_name=cust_name,
                customer_email=cust_email,
                generate_payment_link=False,
            )
        except InsufficientStockError as stock_err:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(stock_err))
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Checkout failed for user %s: %s", user_id, e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Checkout failed: {str(e)}",
            )

    async def get_user_orders(self, user_id: int):
        """Get all orders for a specific user."""
        try:
            orders = await self.order_repo.getUsersAllOrder(user_id=user_id)
            return {
                "success": True,
                "count": len(orders),
                "orders": orders,
            }
        except HTTPException:
            raise
        except Exception:
            logger.exception("Failed to fetch orders for user %s", user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch orders",
            )

    async def cancel_order(self, order_id: int):
        """Cancels an order and safely restores product inventory."""
        try:
            order = await self.order_repo.cancel_order_with_lock(order_id)
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            return {"success": True, "message": "Order cancelled and stock restored", "order": order}
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Failed cancelling order %s: %s", order_id, e)
            raise HTTPException(status_code=500, detail="Failed to cancel order")


orderController = OrderController()
