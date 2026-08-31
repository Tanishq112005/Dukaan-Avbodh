import json
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from langchain_core.messages import HumanMessage
from agents import agent_service
from config.database import db_connection
from models.user import User, UserRole
from sqlmodel import select
from repositories.cart_repository import cart_repository

router = APIRouter()

class ChatRequest(BaseModel):
    user_id: int
    text: str
    cart: List[dict] = []

class EventRequest(BaseModel):
    user_id: int
    event: str
    cart: List[dict] = []

async def sync_cart_and_user(user_id: int, cart_data: list):
    # Ensure the user exists in the DB (for guests) to satisfy the foreign key constraint
    async with db_connection.get_session() as session:
        existing_user = await session.exec(select(User).where(User.id == user_id))
        if not existing_user.first():
            guest_user = User(id=user_id, name=f"Guest {user_id}", role=UserRole.CUSTOMER, identifier=f"guest_{user_id}@dukaan.local")
            session.add(guest_user)
            await session.commit()
    
    await cart_repository.clear_cart(user_id)
    for item in cart_data:
        await cart_repository.add_item(
            user_id=user_id,
            product_id=int(item["id"]),
            quantity=item.get("qty", 1),
            size=item.get("size")
        )

@router.post("/chat/message")
async def chat_message(req: ChatRequest):
    await sync_cart_and_user(req.user_id, req.cart)
    
    config = {"configurable": {"thread_id": str(req.user_id)}}
    human_msg = HumanMessage(content=req.text)
    
    initial_state = {
        "messages": [human_msg],
        "user_id": req.user_id
    }
    
    try:
        result = await agent_service.get_agent().ainvoke(initial_state, config=config)
        ai_reply = result.get("final_response", "Sorry, system error.")
        combo_offer = result.get("combo_offer", None)
        suggested_products = result.get("suggested_products", [])
        
        return {
            "type": "chat_reply", 
            "message": ai_reply,
            "combo_offer": combo_offer,
            "suggested_products": suggested_products
        }
    except Exception as e:
        print(f"[ERROR] Chat agent failed: {e}")
        import traceback
        traceback.print_exc()
        return {"type": "chat_reply", "message": "Sorry, something went wrong. Please try again!"}

@router.post("/chat/event")
async def chat_event(req: EventRequest):
    await sync_cart_and_user(req.user_id, req.cart)
    
    config = {"configurable": {"thread_id": str(req.user_id)}}
    
    if req.event in ["idle_timeout", "viewed_multiple_products", "viewed_checkout", "activity_threshold_reached"]:
        hidden_msg = HumanMessage(content="PROACTIVE_SUGGESTION_TRIGGER")
        try:
            result = await agent_service.get_agent().ainvoke({
                "messages": [hidden_msg],
                "user_id": req.user_id
            }, config=config)
            
            ai_reply = result.get("final_response")
            if ai_reply:
                return {
                    "type": "proactive_suggestion",
                    "message": ai_reply,
                    "combo_offer": result.get("combo_offer", None),
                    "suggested_products": result.get("suggested_products", [])
                }
        except Exception as e:
            print(f"[ERROR] Proactive suggestion failed: {e}")
            import traceback
            traceback.print_exc()
    
    # If no response or invalid event, return empty success
    return {"success": True}
