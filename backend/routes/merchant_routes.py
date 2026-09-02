from fastapi import APIRouter, Depends, HTTPException
from middleware.role_middleware import require_role
from models.user import UserRole
from services.audit_logger import audit_logger
from repositories.chat_audit_repository import chat_audit_repo
from services.analytics_service import analytics_service

router = APIRouter(prefix="/merchant", tags=["Merchant"])

@router.get("/analytics")
async def get_analytics(
    current_user: dict = Depends(require_role(UserRole.MERCHANT))
):
    """Fetch aggregated business analytics, revenue, and AI discount metrics."""
    data = await analytics_service.get_dashboard_metrics()
    return data

@router.get("/audit-logs")
async def get_audit_logs(
    current_user: dict = Depends(require_role(UserRole.MERCHANT))
):
    """Fetch all money/action audit logs from MongoDB."""
    try:
        cursor = audit_logger.collection.find().sort("timestamp", -1).limit(200)
        logs = await cursor.to_list(length=200)
        
        # Convert ObjectId to string for JSON serialization
        for log in logs:
            log["_id"] = str(log["_id"])
            
        return {"logs": logs}
    except Exception as e:
        print(f"[MERCHANT] Could not fetch audit logs: {e}")
        return {"logs": [], "error": "Audit database unavailable"}

@router.get("/chat-threads")
async def get_all_chat_threads(
    current_user: dict = Depends(require_role(UserRole.MERCHANT))
):
    """Fetch all chat threads across all users for auditing."""
    cursor = chat_audit_repo.collection.find().sort("updated_at", -1).limit(100)
    threads = await cursor.to_list(length=100)
    
    for thread in threads:
        thread["_id"] = str(thread["_id"])
        
    return {"threads": threads}

@router.get("/orders")
async def get_all_orders(
    current_user: dict = Depends(require_role(UserRole.MERCHANT))
):
    """Fetch all orders with product and user details for the merchant dashboard."""
    from config.database import db_connection
    from models import Order, Product, User
    from sqlmodel import select
    from sqlalchemy.orm import selectinload
    
    async with db_connection.get_session() as session:
        # Load orders with their related products and users
        statement = select(Order).options(selectinload(Order.product), selectinload(Order.user)).order_by(Order.created_at.desc()).limit(50)
        results = await session.execute(statement)
        orders = results.scalars().all()
        
        # Clean up data to return
        order_list = []
        for order in orders:
            order_list.append({
                "id": order.id,
                "status": order.status,
                "discount_applied": order.discount_applied,
                "razorpay_order_id": order.razorpay_order_id,
                "razorpay_payment_id": order.razorpay_payment_id,
                "created_at": order.created_at,
                "product": {
                    "name": order.product.name if order.product else "Unknown",
                    "image_url": order.product.image_url if order.product else "",
                    "price": order.product.price if order.product else 0,
                },
                "user": {
                    "name": order.user.name if order.user else "Unknown",
                    "email": order.user.identifier if order.user else "Unknown",
                    "address": order.user.address if order.user else "No address provided",
                }
            })
            
        return {"orders": order_list}

from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from agents.merchant import agent_service as merchant_agent_service

class MerchantChatRequest(BaseModel):
    text: str
    thread_id: str = None

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
            "thread_id": thread_id
        }
        
        result = await agent.ainvoke(initial_state, config=config)
        ai_reply = result.get("final_response", "Sorry, system error.")
        
        return {
            "type": "merchant_chat_reply",
            "message": ai_reply
        }
    except Exception as e:
        print(f"[ERROR] Merchant Chat agent failed: {e}")
        import traceback
        traceback.print_exc()
        return {"type": "merchant_chat_reply", "message": "Sorry, something went wrong with the merchant assistant."}
