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
    try:
        await sync_cart_and_user(req.user_id, req.cart)
    except Exception as e:
        print(f"[WARNING] sync_cart_and_user failed during chat_message: {e}")
    
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
        payment_link = result.get("pending_payment_link")
        if payment_link and payment_link not in (ai_reply or ""):
            ai_reply = f"{ai_reply}\n\n[Pay now]({payment_link})\n{payment_link}".strip()
        
        # Fetch the updated cart state after the AI has potentially run MCP tools
        updated_cart = await cart_repository.get_cart_items(req.user_id)
        
        return {
            "type": "chat_reply", 
            "message": ai_reply,
            "combo_offer": combo_offer,
            "suggested_products": suggested_products,
            "cart": updated_cart,
            "ai_discount": result.get("current_discount_percent", 0.0),
            "payment_link": payment_link,
            "payment_link_id": result.get("pending_payment_link_id"),
        }
    except Exception as e:
        print(f"[ERROR] Chat agent failed: {e}")
        import traceback
        traceback.print_exc()
        return {"type": "chat_reply", "message": "Sorry, something went wrong. Please try again!"}

@router.post("/chat/event")
async def chat_event(req: EventRequest):
    config = {"configurable": {"thread_id": str(req.user_id)}}
    
    if req.event == "payment_completed":
        hidden_msg = HumanMessage(content="[SYSTEM EVENT: payment] The customer says they finished paying. Call check_payment_status immediately and tell them the result.")
        try:
            result = await agent_service.get_agent().ainvoke({
                "messages": [hidden_msg],
                "user_id": req.user_id
            }, config=config)
            ai_reply = result.get("final_response")
            updated_cart = await cart_repository.get_cart_items(req.user_id)
            return {
                "type": "chat_reply",
                "message": ai_reply or "Checking your payment now...",
                "combo_offer": result.get("combo_offer", None),
                "suggested_products": result.get("suggested_products", []),
                "cart": updated_cart,
                "ai_discount": result.get("current_discount_percent", 0.0),
            }
        except Exception as e:
            print(f"[ERROR] payment_completed event failed: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": "Could not verify payment yet."}

    if req.event in ["idle_timeout", "viewed_multiple_products", "viewed_checkout", "activity_threshold_reached"]:
        # Let's get the current state to check if we should ignore the trigger (Spam Filter)
        try:
            agent = agent_service.get_agent()
            state_snapshot = agent.get_state(config)
            if state_snapshot and state_snapshot.values and "messages" in state_snapshot.values:
                msgs = state_snapshot.values["messages"]
                # If the last human message was a proactive trigger, ignore this one to prevent spam
                proactive_count = sum(1 for m in msgs[-3:] if isinstance(m, HumanMessage) and m.content == "PROACTIVE_SUGGESTION_TRIGGER")
                if proactive_count > 0:
                    return {"success": True, "ignored": True, "reason": "already triggered recently"}
        except Exception:
            pass

        # Only sync cart if we are actually going to process the event!
        try:
            await sync_cart_and_user(req.user_id, req.cart)
        except Exception as e:
            print(f"[WARNING] sync_cart_and_user failed during event: {e}")

        hidden_msg = HumanMessage(content="PROACTIVE_SUGGESTION_TRIGGER")
        try:
            agent = agent_service.get_agent()
            result = await agent.ainvoke({
                "messages": [hidden_msg],
                "user_id": req.user_id
            }, config=config)
            
            ai_reply = result.get("final_response")
            if ai_reply:
                updated_cart = await cart_repository.get_cart_items(req.user_id)
                return {
                    "type": "proactive_suggestion",
                    "message": ai_reply,
                    "combo_offer": result.get("combo_offer", None),
                    "suggested_products": result.get("suggested_products", []),
                    "cart": updated_cart
                }
        except Exception as e:
            print(f"[ERROR] Proactive suggestion failed: {e}")
            import traceback
            traceback.print_exc()
    
    # If no response or invalid event, return empty success
    return {"success": True}
