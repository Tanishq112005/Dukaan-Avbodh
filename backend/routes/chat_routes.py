import json
import traceback
from typing import List, Optional
from fastapi import APIRouter
from langchain_core.messages import HumanMessage
from sqlmodel import select

from agents.user import agent_service
from config.database import db_connection
from User.models import User, UserRole
from Cart.database import cart_repository
from Chat.models import ChatMessage, ThreadState
from Chat.schemas import ChatRequest, EventRequest
from Chat.database import chat_audit_repo

router = APIRouter()


async def sync_cart_and_user(user_id: int, cart_data: list):
    """
    Ensure the user exists in the DB (for guests) to satisfy the foreign key constraint,
    then bulk-sync their cart items in a single transaction.
    """
    async with db_connection.get_session() as session:
        existing_user = await session.exec(select(User).where(User.id == user_id))
        if not existing_user.first():
            guest_user = User(
                id=user_id,
                name=f"Guest {user_id}",
                role=UserRole.CUSTOMER,
                email=f"guest_{user_id}@dukaan.local"
            )
            session.add(guest_user)
            await session.commit()

    await cart_repository.sync_items(user_id, cart_data)


@router.post("/chat/message")
async def chat_message(req: ChatRequest):
    try:
        await sync_cart_and_user(req.user_id, req.cart)
    except Exception as e:
        print(f"[WARNING] sync_cart_and_user failed during chat_message: {e}")

    thread_id_val = req.thread_id or str(req.user_id)
    config = {"configurable": {"thread_id": thread_id_val}}
    human_msg = HumanMessage(content=req.text)

    initial_state = {
        "messages": [human_msg],
        "user_id": req.user_id,
        "thread_id": thread_id_val,
    }

    try:
        # Audit user message
        await chat_audit_repo.get_or_create_thread(req.user_id, thread_id_val)
        await chat_audit_repo.add_message(
            req.user_id,
            thread_id_val,
            ChatMessage(sender="human", message=req.text)
        )

        # Invoke LangGraph conversation agent
        result = await agent_service.get_agent().ainvoke(initial_state, config=config)

        ai_reply = result.get("final_response", "Sorry, system error.")
        combo_offer = result.get("combo_offer", None)
        suggested_products = result.get("suggested_products", [])
        payment_link = result.get("pending_payment_link")
        current_discount = result.get("current_discount_percent", 0.0)

        # Save AI reply to audit log
        await chat_audit_repo.add_message(
            req.user_id,
            thread_id_val,
            ChatMessage(sender="ai", message=ai_reply)
        )

        # Update thread state in audit storage
        await chat_audit_repo.update_state_patch(req.user_id, thread_id_val, {
            "current_discount_percent": current_discount,
            "combo_offer": combo_offer
        })

        # Dispatch background state archival and rolling summarization to queue
        try:
            from task_queue.sendingResult import sendingResult

            queue_payload = {
                "thread_id": thread_id_val,
                "user_id": req.user_id,
                "messages": result.get("messages", [human_msg]),
                "conversation_summary": result.get("conversation_summary", ""),
                "important_facts": result.get("important_facts", {})
            }
            await sendingResult.sendData(queue_payload)
        except Exception as q_err:
            print(f"[WARNING] Failed to dispatch chat state to background queue: {q_err}")

        # Fetch the updated cart state after the AI has potentially run MCP tools
        updated_cart = await cart_repository.get_items(req.user_id)

        return {
            "type": "chat_reply",
            "message": ai_reply,
            "combo_offer": combo_offer,
            "suggested_products": suggested_products,
            "cart": updated_cart,
            "ai_discount": current_discount,
            "payment_link": payment_link,
            "payment_link_id": result.get("pending_payment_link_id"),
        }

    except Exception as e:
        print(f"[ERROR] Chat agent failed: {e}")
        traceback.print_exc()
        return {
            "type": "chat_reply",
            "message": "Sorry, something went wrong. Please try again!"
        }


@router.post("/chat/event")
async def chat_event(req: EventRequest):
    thread_id_val = req.thread_id or str(req.user_id)
    config = {"configurable": {"thread_id": thread_id_val}}

    # Event 1: Combo Declined
    if req.event == "combo_declined":
        try:
            agent = agent_service.get_agent()
            await agent.aupdate_state(config, {"combo_offer": None})
        except Exception as e:
            print(f"[WARNING] combo_declined langgraph update failed: {e}")

        try:
            await chat_audit_repo.update_state_patch(req.user_id, thread_id_val, {"combo_offer": None})
        except Exception as e:
            print(f"[WARNING] combo_declined audit update failed: {e}")

        return {"type": "combo_cleared", "combo_offer": None}

    # Event 2: Payment Completed
    if req.event == "payment_completed":
        hidden_msg = HumanMessage(
            content="[SYSTEM EVENT: payment] The customer says they finished paying. Call check_payment_status immediately and tell them the result."
        )
        try:
            result = await agent_service.get_agent().ainvoke({
                "messages": [hidden_msg],
                "user_id": req.user_id,
                "thread_id": thread_id_val,
            }, config=config)

            ai_reply = result.get("final_response")
            updated_cart = await cart_repository.get_items(req.user_id)

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
            traceback.print_exc()
            return {"success": False, "error": "Could not verify payment yet."}

    # Event 3: Proactive Suggestion Triggers
    if req.event in ["idle_timeout", "viewed_multiple_products", "viewed_checkout", "activity_threshold_reached"]:
        # Spam Filter check
        try:
            agent = agent_service.get_agent()
            state_snapshot = agent.get_state(config)
            if state_snapshot and state_snapshot.values and "messages" in state_snapshot.values:
                msgs = state_snapshot.values["messages"]
                proactive_count = sum(
                    1 for m in msgs[-3:]
                    if isinstance(m, HumanMessage) and m.content == "PROACTIVE_SUGGESTION_TRIGGER"
                )
                if proactive_count > 0:
                    return {"success": True, "ignored": True, "reason": "already triggered recently"}
        except Exception:
            pass

        # Sync cart for proactive processing
        try:
            await sync_cart_and_user(req.user_id, req.cart)
        except Exception as e:
            print(f"[WARNING] sync_cart_and_user failed during event: {e}")

        hidden_msg = HumanMessage(content="PROACTIVE_SUGGESTION_TRIGGER")
        try:
            await chat_audit_repo.get_or_create_thread(req.user_id, thread_id_val)
            await chat_audit_repo.add_message(
                req.user_id,
                thread_id_val,
                ChatMessage(sender="system", message=f"Event triggered: {req.event}")
            )

            agent = agent_service.get_agent()
            result = await agent.ainvoke({
                "messages": [hidden_msg],
                "user_id": req.user_id,
                "thread_id": thread_id_val,
            }, config=config)

            ai_reply = result.get("final_response")
            if ai_reply:
                await chat_audit_repo.add_message(
                    req.user_id,
                    thread_id_val,
                    ChatMessage(sender="ai", message=ai_reply)
                )
                await chat_audit_repo.update_state_patch(req.user_id, thread_id_val, {
                    "current_discount_percent": result.get("current_discount_percent", 0.0),
                    "combo_offer": result.get("combo_offer", None)
                })

                updated_cart = await cart_repository.get_items(req.user_id)
                return {
                    "type": "proactive_suggestion",
                    "message": ai_reply,
                    "combo_offer": result.get("combo_offer", None),
                    "suggested_products": result.get("suggested_products", []),
                    "cart": updated_cart
                }

        except Exception as e:
            print(f"[ERROR] Proactive suggestion failed: {e}")
            traceback.print_exc()

    # If no response or unknown event, return empty success
    return {"success": True}
