import os
from typing import Optional
from sqlmodel import select
from config.database import db_connection
from models.order import Order

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_TWV2ichCwzRcvo")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "9Ew8lMz1DUumk4hYVPBbf4dd")

try:
    import razorpay
    rzp_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
except Exception:
    rzp_client = None


async def mark_orders_paid(
    *,
    user_id: Optional[int] = None,
    payment_link_id: Optional[str] = None,
    razorpay_order_id: Optional[str] = None,
    razorpay_payment_id: Optional[str] = None,
) -> int:
    """Mark matching pending orders as paid. Returns number of rows updated."""
    async with db_connection.get_session() as session:
        query = select(Order)
        if payment_link_id:
            query = query.where(Order.razorpay_payment_link_id == payment_link_id)
        elif razorpay_order_id:
            query = query.where(Order.razorpay_order_id == razorpay_order_id)
        elif user_id is not None:
            query = query.where(Order.user_id == user_id).where(
                Order.status.in_(["pending_payment", "confirmed", "pending"])
            )
        else:
            return 0

        orders = (await session.exec(query)).all()
        updated = 0
        for order in orders:
            order.status = "paid"
            if razorpay_payment_id:
                order.razorpay_payment_id = razorpay_payment_id
            session.add(order)
            updated += 1
        if updated:
            await session.commit()
        return updated


async def get_latest_pending_payment(user_id: int) -> Optional[Order]:
    async with db_connection.get_session() as session:
        result = await session.exec(
            select(Order)
            .where(Order.user_id == user_id)
            .where(Order.razorpay_payment_link_id != None)
            .order_by(Order.created_at.desc())
        )
        return result.first()


async def check_user_payment_status(user_id: int) -> dict:
    """Poll Razorpay (and local DB) for the user's latest payment link."""
    order = await get_latest_pending_payment(user_id)
    if not order:
        return {
            "success": True,
            "paid": False,
            "status": "none",
            "message": "No payment link found for this user.",
        }

    if order.status == "paid" or order.razorpay_payment_id:
        return {
            "success": True,
            "paid": True,
            "status": "paid",
            "payment_link": order.payment_link_url,
            "razorpay_payment_id": order.razorpay_payment_id,
            "message": "Payment is complete.",
        }

    link_status = None
    payment_id = None
    if rzp_client and order.razorpay_payment_link_id:
        try:
            pl = rzp_client.payment_link.fetch(order.razorpay_payment_link_id)
            link_status = pl.get("status")
            payments = pl.get("payments") or []
            if payments:
                payment_id = payments[0].get("payment_id") or payments[0].get("id")
        except Exception as e:
            print(f"[RAZORPAY] payment_link.fetch failed: {e}")

    paid = link_status == "paid"
    if paid:
        await mark_orders_paid(
            user_id=user_id,
            payment_link_id=order.razorpay_payment_link_id,
            razorpay_payment_id=payment_id,
        )

    return {
        "success": True,
        "paid": paid,
        "status": link_status or order.status,
        "payment_link": order.payment_link_url,
        "payment_link_id": order.razorpay_payment_link_id,
        "razorpay_payment_id": payment_id or order.razorpay_payment_id,
        "message": "Payment is complete." if paid else "Payment is not complete yet. Ask the customer to finish paying on the link.",
    }
