import logging
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

from rabbitmq.producer import rabbitProducer
from Order.models import Order as OrderModel

logger = logging.getLogger(__name__)


async def enqueue_order_confirmation_notification(
    orders: List[OrderModel],
    user_id: Optional[int] = None,
    customer_email: Optional[str] = None,
    customer_name: Optional[str] = None,
    shipping_address: Optional[str] = None,
) -> bool:
    """
    Constructs an order receipt slip from confirmed orders and enqueues
    an order_confirmation task to RabbitMQ for email delivery.
    """
    if not orders:
        logger.debug("[OrderNotification] No orders provided to notify.")
        return False

    effective_uid = user_id or orders[0].user_id
    user_obj = None

    if effective_uid:
        try:
            # Lazy import to prevent circular import between User and Order
            from User.database import userRepository
            user_obj = await userRepository.get_by_id(effective_uid)
        except Exception as e:
            logger.warning("[OrderNotification] Could not fetch user %s: %s", effective_uid, e)

    # Determine recipient email
    recipient_email = customer_email
    if not recipient_email and user_obj and user_obj.email:
        raw_email = str(user_obj.email).strip()
        # Avoid sending emails to dummy or guest domains
        if not raw_email.endswith("@dukaan.local") and not raw_email.startswith("guest_"):
            recipient_email = raw_email

    if not recipient_email:
        logger.info(
            "[OrderNotification] Order #%s belongs to guest (%s). Skipping email notification.",
            orders[0].id,
            user_obj.email if user_obj else effective_uid,
        )
        return False

    recipient_name = customer_name or (user_obj.name if user_obj else "Customer")
    delivery_address = shipping_address or (user_obj.address if user_obj else None) or "Standard Delivery Address"

    # Build order items list and calculate totals
    items_list: List[Dict[str, Any]] = []
    total_amount = 0.0
    max_discount_applied = 0.0

    for o in orders:
        total_amount += float(o.total_amount or 0.0)
        max_discount_applied = max(max_discount_applied, float(o.discount_applied or 0.0))

        prod = getattr(o, "product", None)
        p_name = prod.name if prod else f"Product #{o.product_id}"
        p_brand = prod.brand if prod else "Dukaan"
        p_price = float(prod.price) if prod else float(o.total_amount or 0.0)
        p_img = prod.image_url if prod else None

        items_list.append({
            "product_id": o.product_id,
            "name": p_name,
            "brand": p_brand,
            "quantity": o.quantity or 1,
            "price": p_price,
            "total_amount": float(o.total_amount or 0.0),
            "discount_percentage": float(o.discount_applied or 0.0),
            "image_url": p_img,
        })

    order_ids_str = ", ".join(str(o.id) for o in orders)
    primary_order = orders[0]
    payment_id = getattr(primary_order, "gateway_payment_id", None) or "PAID_CONFIRMED"

    order_slip_data: Dict[str, Any] = {
        "order_id": order_ids_str,
        "primary_order_id": primary_order.id,
        "customer_name": recipient_name,
        "items": items_list,
        "total_amount": round(total_amount, 2),
        "discount_applied": round(max_discount_applied, 2),
        "gateway_payment_id": payment_id,
        "shipping_address": delivery_address,
        "order_date": datetime.now().strftime("%B %d, %Y, %I:%M %p"),
        "currency": "INR",
    }

    try:
        # Publish to RabbitMQ queue via producer
        published = await rabbitProducer.publish_notification(
            event_type="order_confirmation",
            recipient=recipient_email,
            data={"order_data": order_slip_data},
        )
        logger.info(
            "[OrderNotification] Successfully enqueued order confirmation slip for orders [%s] to <%s>",
            order_ids_str,
            recipient_email,
        )
        return published
    except Exception as exc:
        logger.error("[OrderNotification] Failed enqueuing order confirmation for %s: %s", order_ids_str, exc)
        return False
