import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status

from Order.database import OrderRepository, orderRepository, InsufficientStockError
from Payment.controller import paymentController
from Order.schemas import CheckoutRequest
from Order.models import Order as OrderModel

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
                generate_payment_link=True,
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

    def format_order_summary(self, order: OrderModel) -> Dict[str, Any]:
        """Formats an OrderModel instance into a clean dictionary with product metadata."""
        product_info = None
        if getattr(order, "product", None):
            p = order.product
            product_info = {
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "image_url": p.image_url or (f"https://picsum.photos/seed/{p.id}/400/500" if p.id else None),
                "brand": p.brand,
                "type": p.type.value if hasattr(p.type, "value") else str(p.type),
            }

        created_dt = order.created_at
        now = datetime.now()
        hours_since = (now - created_dt).total_seconds() / 3600.0 if created_dt else 0.0

        payment_st = str(order.payment_status or "pending").lower()
        if payment_st in ["cancelled", "refunded"]:
            tracking_status = "cancelled"
            stage = "Cancelled"
        elif payment_st in ["paid", "completed"]:
            if hours_since < 6:
                tracking_status = "processing"
                stage = "Quality Check"
            elif hours_since < 24:
                tracking_status = "shipped"
                stage = "Dispatched"
            elif hours_since < 48:
                tracking_status = "out_for_delivery"
                stage = "Out for Delivery"
            else:
                tracking_status = "delivered"
                stage = "Delivered"
        else:
            tracking_status = "placed"
            stage = "Order Placed"

        return {
            "order_id": order.id,
            "product_id": order.product_id,
            "quantity": order.quantity,
            "total_amount": float(order.total_amount or 0.0),
            "discount_applied": float(order.discount_applied or 0.0),
            "payment_status": payment_st,
            "tracking_status": tracking_status,
            "stage": stage,
            "delivery_estimate": "3-5 Business Days",
            "gateway_order_id": order.gateway_order_id,
            "payment_link_url": order.payment_link_url,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "product": product_info,
        }

    async def get_user_orders(self, user_id: int):
        """Get all orders for a specific user with enriched product data."""
        try:
            orders = await self.order_repo.getUsersAllOrder(user_id=user_id)
            summaries = [self.format_order_summary(o) for o in orders]
            return {
                "success": True,
                "count": len(summaries),
                "orders": summaries,
            }
        except HTTPException:
            raise
        except Exception:
            logger.exception("Failed to fetch orders for user %s", user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch orders",
            )

    async def get_order_by_id(self, order_id: int, user_id: Optional[int] = None):
        """Fetch a single order by ID, optionally verifying user ownership."""
        order = await self.order_repo.get_order_by_id(order_id)
        if not order:
            return None
        if user_id and order.user_id != user_id:
            return None
        return order

    async def get_order_tracking(self, order_id: Optional[int] = None, user_id: Optional[int] = None):
        """Fetches live tracking status for an order or user's most recent order."""
        if order_id:
            order = await self.order_repo.get_order_by_id(order_id)
            if not order:
                return {"success": False, "error": f"Order #{order_id} not found."}
            if user_id and order.user_id != user_id:
                return {"success": False, "error": f"Order #{order_id} does not belong to your account."}
        elif user_id:
            orders = await self.order_repo.getUsersAllOrder(user_id)
            if not orders:
                return {"success": False, "error": "No orders found in your order history."}
            order = orders[0]
        else:
            return {"success": False, "error": "Please provide either an order_id or user_id to track."}

        summary = self.format_order_summary(order)
        return {
            "success": True,
            "order_id": summary["order_id"],
            "status": summary["tracking_status"],
            "stage": summary["stage"],
            "delivery_estimate": summary["delivery_estimate"],
            "payment_status": summary["payment_status"],
            "amount": summary["total_amount"],
            "items": [summary["product"]] if summary.get("product") else [],
            "order": summary,
        }

    async def cancel_order(self, order_id: int):
        """Cancels an order and safely restores product inventory."""
        try:
            order = await self.order_repo.cancel_order_with_lock(order_id)
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            summary = self.format_order_summary(order)
            return {"success": True, "message": "Order cancelled and stock restored", "order": summary}
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Failed cancelling order %s: %s", order_id, e)
            raise HTTPException(status_code=500, detail="Failed to cancel order")


orderController = OrderController()
