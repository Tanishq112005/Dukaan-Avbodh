import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from middleware.merchant_middleware import require_role
from User.models import UserRole
from services.audit_logger import audit_logger
from Chat.database import chat_audit_repo
from services.analytics_service import analytics_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/merchant", tags=["Merchant"])


@router.get("/analytics")
async def get_analytics(
    time_range: str = Query("all", description="Time window for metrics: 'today', '7d', '30d', or 'all'"),
    current_user: dict = Depends(require_role(UserRole.MERCHANT))
):
    """Fetch aggregated business analytics, revenue, top selling items, and AI discount metrics."""
    data = await analytics_service.get_dashboard_metrics(time_range=time_range)
    return data


@router.get("/audit-logs")
async def get_audit_logs(
    current_user: dict = Depends(require_role(UserRole.MERCHANT))
):
    """Fetch all money/action audit logs from MongoDB."""
    try:
        cursor = audit_logger.collection.find().sort("timestamp", -1).limit(200)
        logs = await cursor.to_list(length=200)

        # Convert ObjectId and datetime for JSON serialization
        for log in logs:
            log["_id"] = str(log["_id"])
            if "timestamp" in log and isinstance(log["timestamp"], datetime):
                log["timestamp"] = log["timestamp"].isoformat()

        return {"logs": logs}
    except Exception as e:
        logger.exception("[MERCHANT] Could not fetch audit logs: %s", e)
        return {"logs": [], "error": "Audit database unavailable"}


@router.get("/chat-threads")
async def get_all_chat_threads(
    current_user: dict = Depends(require_role(UserRole.MERCHANT))
):
    """Fetch all chat threads across all users for auditing and transcript inspection."""
    try:
        cursor = chat_audit_repo.collection.find().sort("updated_at", -1).limit(100)
        threads = await cursor.to_list(length=100)

        for thread in threads:
            thread["_id"] = str(thread["_id"])
            if "created_at" in thread and isinstance(thread["created_at"], datetime):
                thread["created_at"] = thread["created_at"].isoformat()
            if "updated_at" in thread and isinstance(thread["updated_at"], datetime):
                thread["updated_at"] = thread["updated_at"].isoformat()

            if "messages" in thread and isinstance(thread["messages"], list):
                for m in thread["messages"]:
                    if isinstance(m, dict) and "timestamp" in m and isinstance(m["timestamp"], datetime):
                        m["timestamp"] = m["timestamp"].isoformat()

            # Ensure state timestamps are serialized
            st = thread.get("state")
            if isinstance(st, dict):
                logs = st.get("negotiation_log")
                if isinstance(logs, list):
                    for l in logs:
                        if isinstance(l, dict) and "timestamp" in l and isinstance(l["timestamp"], datetime):
                            l["timestamp"] = l["timestamp"].isoformat()

        return {"threads": threads}
    except Exception as e:
        logger.exception("[MERCHANT] Could not fetch chat threads: %s", e)
        return {"threads": [], "error": "Chat database unavailable"}


@router.get("/orders")
async def get_all_orders(
    current_user: dict = Depends(require_role(UserRole.MERCHANT))
):
    """Fetch all orders with product and user details for the merchant dashboard."""
    from config.database import db_connection
    from Order.models import Order
    from Product.models import Product
    from User.models import User
    from sqlmodel import select
    from sqlalchemy.orm import joinedload

    async with db_connection.get_session() as session:
        # Load orders with their related products and users
        statement = (
            select(Order)
            .options(joinedload(Order.product), joinedload(Order.user))
            .order_by(Order.created_at.desc())
            .limit(100)
        )
        results = await session.execute(statement)
        orders = results.scalars().all()

        grouped_orders = {}
        for order in orders:
            group_id = order.gateway_order_id or str(order.id)
            if group_id not in grouped_orders:
                grouped_orders[group_id] = {
                    "id": group_id,
                    "order_id": order.id,
                    "status": order.payment_status or "placed",
                    "payment_status": order.payment_status or "placed",
                    "discount_applied": float(order.discount_applied or 0.0),
                    "razorpay_order_id": order.gateway_order_id,
                    "razorpay_payment_id": order.gateway_payment_id,
                    "total_amount": float(order.total_amount or 0.0),
                    "created_at": order.created_at.isoformat() if order.created_at else None,
                    "products": [],
                    "user": {
                        "id": order.user.id if order.user else None,
                        "name": order.user.name if order.user else "Customer",
                        "email": order.user.email if order.user else "customer@dukaan.local",
                        "address": order.user.address if order.user and order.user.address else "Bangalore, India",
                    },
                }

            if order.product:
                grouped_orders[group_id]["products"].append({
                    "id": order.product.id,
                    "name": order.product.name,
                    "image_url": order.product.image_url,
                    "price": float(order.product.price),
                    "cost_price": float(order.product.cost_price or 0.0),
                    "brand": order.product.brand or "Dukaan",
                    "quantity": order.quantity or 1,
                })

        return {"orders": list(grouped_orders.values())}


from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from agents.merchant import agent_service as merchant_agent_service


class MerchantChatRequest(BaseModel):
    text: str
    thread_id: Optional[str] = None


@router.post("/chat")
async def chat_with_merchant_agent(
    req: MerchantChatRequest,
    current_user: dict = Depends(require_role(UserRole.MERCHANT))
):
    try:
        agent = merchant_agent_service.get_merchant_agent()
        user_id = current_user.get("user_id")
        thread_id = req.thread_id or f"merchant_{user_id}"
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "messages": [HumanMessage(content=req.text)],
            "user_id": user_id,
            "thread_id": thread_id,
        }

        result = await agent.ainvoke(initial_state, config=config)
        ai_reply = result.get("final_response", "Sorry, system error.")

        return {
            "type": "merchant_chat_reply",
            "message": ai_reply,
        }
    except Exception as e:
        logger.exception("[ERROR] Merchant Chat agent failed: %s", e)
        return {
            "type": "merchant_chat_reply",
            "message": "Sorry, something went wrong with the merchant assistant.",
        }
