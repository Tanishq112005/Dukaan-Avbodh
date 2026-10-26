import re
import json
import asyncio
import logging
from typing import Optional, Dict, Any, List, AsyncGenerator
from fastapi import HTTPException
from langchain_core.messages import HumanMessage
from sqlmodel import select

from agents.user import agent_service
from config.database import db_connection
from User.models import User, UserRole
from Cart.database import cart_repository
from Chat.models import ChatMessage
from Chat.schemas import ChatRequest, EventRequest
from Chat.database import chat_audit_repo
from utils.text_cleaning import clean_ai_output

logger = logging.getLogger(__name__)


class UserController:
    """
    Controller for the User AI Chat Agent.
    Orchestrates user-cart synchronization, Redis memory hydration,
    LangGraph execution, streaming SSE responses, and background summarization queueing.
    """

    def __init__(self, service=None, audit_repo=None, cart_repo=None):
        self.agent_service = service or agent_service
        self.audit_repo = audit_repo or chat_audit_repo
        self.cart_repo = cart_repo or cart_repository

    async def sync_cart_and_user(self, user_id: int, cart_data: list):
        """
        Ensures the customer/guest exists in SQL database (satisfying foreign keys),
        and bulk-syncs their cart items in a single transaction.
        """
        async with db_connection.get_session() as session:
            existing_user = await session.exec(select(User).where(User.id == user_id))
            if not existing_user.first():
                guest_user = User(
                    id=user_id,
                    name=f"Guest {user_id}",
                    role=UserRole.CUSTOMER,
                    email=f"guest_{user_id}@dukaan.local",
                )
                session.add(guest_user)
                await session.commit()

        await self.cart_repo.sync_items(user_id, cart_data)

    async def _prepare_initial_state(self, user_id: int, thread_id_val: str, human_msg: HumanMessage):
        """
        Hydrates cached conversation summary and important customer facts from Redis.
        """
        cached_summary = None
        cached_facts = None
        try:
            from config.redis import redisClient
            r_client = redisClient.get_redis_client()
            raw_cached = r_client.get(f"agent_state:{thread_id_val}")
            if raw_cached:
                cached_data = json.loads(raw_cached)
                cached_summary = cached_data.get("conversation_summary")
                cached_facts = cached_data.get("important_facts")
        except Exception as cache_err:
            logger.warning("Could not read cached agent state: %s", cache_err)

        initial_state = {
            "messages": [human_msg],
            "user_id": user_id,
            "thread_id": thread_id_val,
        }
        if cached_summary:
            initial_state["conversation_summary"] = cached_summary
        if cached_facts:
            initial_state["important_facts"] = cached_facts

        return initial_state, cached_summary, cached_facts

    async def _post_process_chat_completion(
        self,
        user_id: int,
        thread_id_val: str,
        state: dict,
        cached_summary: Optional[str],
        cached_facts: Optional[Any],
        human_msg: HumanMessage,
    ) -> dict:
        """
        Audits AI reply, syncs thread patch to MongoDB, queues rolling summary task,
        and constructs final response payload.
        """
        ai_reply = state.get("final_response")
        if not ai_reply:
            messages = state.get("messages", [])
            for msg in reversed(messages):
                msg_type = getattr(msg, "type", "")
                content = getattr(msg, "content", "")
                has_tool_calls = bool(getattr(msg, "tool_calls", None))
                if (msg_type == "ai" or hasattr(msg, "tool_calls")) and not has_tool_calls and content:
                    ai_reply = str(content)
                    break
        ai_reply = clean_ai_output(ai_reply) if ai_reply else "Sorry, system error."
        combo_offer = state.get("combo_offer", None)
        raw_suggested = state.get("suggested_products", [])
        suggested_products = []
        for p in raw_suggested:
            if isinstance(p, dict) and "product" in p and isinstance(p["product"], dict):
                prod_info = dict(p["product"])
                if "id" not in prod_info and "product_id" in p:
                    prod_info["id"] = p["product_id"]
                suggested_products.append(prod_info)
            elif isinstance(p, dict):
                suggested_products.append(p)
        payment_link = state.get("pending_payment_link")
        payment_link_id = state.get("pending_payment_link_id")
        current_discount = state.get("current_discount_percent", 0.0)

        # Save AI reply to audit log
        await self.audit_repo.add_message(
            user_id,
            thread_id_val,
            ChatMessage(sender="ai", message=ai_reply),
        )

        # Update thread state in audit storage
        await self.audit_repo.update_state_patch(
            user_id,
            thread_id_val,
            {
                "current_discount_percent": current_discount,
                "combo_offer": combo_offer,
            },
        )

        # Dispatch background state archival and rolling summarization to queue
        try:
            from task_queue.sendingResult import sendingResult

            queue_payload = {
                "thread_id": thread_id_val,
                "user_id": user_id,
                "messages": state.get("messages", [human_msg]),
                "conversation_summary": state.get("conversation_summary") or cached_summary or "",
                "important_facts": state.get("important_facts") or cached_facts or {},
            }
            await sendingResult.sendData(queue_payload)
        except Exception as q_err:
            logger.warning("Failed to dispatch chat state to background queue: %s", q_err)

        # Fetch the updated cart state after the AI has potentially run MCP tools
        updated_cart = await self.cart_repo.get_items(user_id)

        return {
            "type": "chat_reply",
            "message": ai_reply,
            "combo_offer": combo_offer,
            "suggested_products": suggested_products,
            "cart": updated_cart,
            "ai_discount": current_discount,
            "payment_link": payment_link,
            "payment_link_id": payment_link_id,
        }

    async def process_message(self, req: ChatRequest) -> dict:
        """
        Synchronous non-streaming execution for chat messages.
        """
        try:
            await self.sync_cart_and_user(req.user_id, req.cart)
        except Exception as e:
            logger.warning("sync_cart_and_user failed during process_message: %s", e)

        thread_id_val = req.thread_id or str(req.user_id)
        config = {"configurable": {"thread_id": thread_id_val}}
        human_msg = HumanMessage(content=req.text)

        initial_state, cached_summary, cached_facts = await self._prepare_initial_state(
            req.user_id, thread_id_val, human_msg
        )

        try:
            # Audit user message
            await self.audit_repo.get_or_create_thread(req.user_id, thread_id_val)
            await self.audit_repo.add_message(
                req.user_id,
                thread_id_val,
                ChatMessage(sender="human", message=req.text),
            )

            # Invoke LangGraph conversation agent
            agent = await self.agent_service.get_agent_async()
            result = await agent.ainvoke(initial_state, config=config)

            return await self._post_process_chat_completion(
                req.user_id, thread_id_val, result, cached_summary, cached_facts, human_msg
            )

        except Exception as e:
            logger.exception("Chat agent failed in process_message: %s", e)
            return {
                "type": "chat_reply",
                "message": "Sorry, something went wrong. Please try again!",
            }

    async def stream_message(self, req: ChatRequest) -> AsyncGenerator[str, None]:
        """
        Streams LangGraph execution events, node state updates, token deltas,
        and final structured chat reply via Server-Sent Events (SSE).
        """
        try:
            await self.sync_cart_and_user(req.user_id, req.cart)
        except Exception as e:
            logger.warning("sync_cart_and_user failed during stream_message: %s", e)

        thread_id_val = req.thread_id or str(req.user_id)
        config = {"configurable": {"thread_id": thread_id_val}}
        human_msg = HumanMessage(content=req.text)

        initial_state, cached_summary, cached_facts = await self._prepare_initial_state(
            req.user_id, thread_id_val, human_msg
        )

        try:
            # Audit user message
            await self.audit_repo.get_or_create_thread(req.user_id, thread_id_val)
            await self.audit_repo.add_message(
                req.user_id,
                thread_id_val,
                ChatMessage(sender="human", message=req.text),
            )

            # Signal stream initiation
            yield f"data: {json.dumps({'type': 'stream_start', 'thread_id': thread_id_val})}\n\n"

            agent = await self.agent_service.get_agent_async()
            latest_state = dict(initial_state)

            async for mode, chunk in agent.astream(
                initial_state,
                config=config,
                stream_mode=["updates", "values"],
            ):
                if mode == "updates" and isinstance(chunk, dict):
                    for node_name, updates in chunk.items():
                        if not isinstance(updates, dict):
                            continue
                        node_payload = {
                            "type": "node_update",
                            "node": node_name,
                        }
                        if "intent" in updates:
                            node_payload["intent"] = updates["intent"]
                        if "gender" in updates:
                            node_payload["gender"] = updates["gender"]
                        if "suggested_products" in updates:
                            node_payload["suggested_products"] = updates["suggested_products"]
                        if "current_discount_percent" in updates:
                            node_payload["current_discount_percent"] = updates["current_discount_percent"]
                        if "cart_total" in updates:
                            node_payload["cart_total"] = updates["cart_total"]
                        if "cart" in updates:
                            node_payload["cart"] = updates["cart"]
                        if "combo_offer" in updates:
                            node_payload["combo_offer"] = updates["combo_offer"]
                        if "final_response" in updates:
                            node_payload["final_response"] = clean_ai_output(updates["final_response"])

                        yield f"data: {json.dumps(node_payload)}\n\n"

                elif mode == "values" and isinstance(chunk, dict):
                    latest_state.update(chunk)

            # Final response assembly and persistence
            final_payload = await self._post_process_chat_completion(
                req.user_id, thread_id_val, latest_state, cached_summary, cached_facts, human_msg
            )

            # Stream message tokens for typing animations
            message_text = final_payload.get("message", "")
            if message_text:
                words = re.split(r"(\s+)", message_text)
                for w in words:
                    if w:
                        yield f"data: {json.dumps({'type': 'token', 'content': w})}\n\n"
                        await asyncio.sleep(0.005)

            # Complete payload and termination marker
            yield f"data: {json.dumps(final_payload)}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.exception("Error during stream_message: %s", e)
            error_payload = {
                "type": "chat_reply",
                "message": "Sorry, something went wrong while processing your request.",
                "error": str(e),
            }
            yield f"data: {json.dumps(error_payload)}\n\n"
            yield "data: [DONE]\n\n"

    async def process_event(self, req: EventRequest) -> dict:
        """
        Synchronous non-streaming execution for system/UI triggered events.
        """
        thread_id_val = req.thread_id or str(req.user_id)
        config = {"configurable": {"thread_id": thread_id_val}}

        # Event 1: Combo Declined
        if req.event == "combo_declined":
            try:
                agent = await self.agent_service.get_agent_async()
                await agent.aupdate_state(config, {"combo_offer": None})
            except Exception as e:
                logger.warning("combo_declined langgraph update failed: %s", e)

            try:
                await self.audit_repo.update_state_patch(req.user_id, thread_id_val, {"combo_offer": None})
            except Exception as e:
                logger.warning("combo_declined audit update failed: %s", e)

            return {"type": "combo_cleared", "combo_offer": None}

        # Event 2: Payment Completed
        if req.event == "payment_completed":
            hidden_msg = HumanMessage(
                content="[SYSTEM EVENT: payment] The customer says they finished paying. Call check_payment_status immediately and tell them the result."
            )
            try:
                agent = await self.agent_service.get_agent_async()
                result = await agent.ainvoke(
                    {
                        "messages": [hidden_msg],
                        "user_id": req.user_id,
                        "thread_id": thread_id_val,
                    },
                    config=config,
                )

                ai_reply = result.get("final_response")
                updated_cart = await self.cart_repo.get_items(req.user_id)

                return {
                    "type": "chat_reply",
                    "message": ai_reply or "Checking your payment now...",
                    "combo_offer": result.get("combo_offer", None),
                    "suggested_products": result.get("suggested_products", []),
                    "cart": updated_cart,
                    "ai_discount": result.get("current_discount_percent", 0.0),
                }
            except Exception as e:
                logger.exception("payment_completed event failed: %s", e)
                return {"success": False, "error": "Could not verify payment yet."}

        # Event 3: Proactive Suggestion Triggers
        if req.event in ["idle_timeout", "viewed_multiple_products", "viewed_checkout", "activity_threshold_reached"]:
            try:
                agent = await self.agent_service.get_agent_async()
                state_snapshot = agent.get_state(config)
                if state_snapshot and state_snapshot.values and "messages" in state_snapshot.values:
                    msgs = state_snapshot.values["messages"]
                    proactive_count = sum(
                        1
                        for m in msgs[-3:]
                        if isinstance(m, HumanMessage) and m.content == "PROACTIVE_SUGGESTION_TRIGGER"
                    )
                    if proactive_count > 0:
                        return {"success": True, "ignored": True, "reason": "already triggered recently"}
            except Exception:
                pass

            try:
                await self.sync_cart_and_user(req.user_id, req.cart)
            except Exception as e:
                logger.warning("sync_cart_and_user failed during proactive event: %s", e)

            hidden_msg = HumanMessage(content="PROACTIVE_SUGGESTION_TRIGGER")
            try:
                await self.audit_repo.get_or_create_thread(req.user_id, thread_id_val)
                await self.audit_repo.add_message(
                    req.user_id,
                    thread_id_val,
                    ChatMessage(sender="system", message=f"Event triggered: {req.event}"),
                )

                agent = await self.agent_service.get_agent_async()
                result = await agent.ainvoke(
                    {
                        "messages": [hidden_msg],
                        "user_id": req.user_id,
                        "thread_id": thread_id_val,
                    },
                    config=config,
                )

                ai_reply = result.get("final_response")
                if ai_reply:
                    await self.audit_repo.add_message(
                        req.user_id,
                        thread_id_val,
                        ChatMessage(sender="ai", message=ai_reply),
                    )
                    await self.audit_repo.update_state_patch(
                        req.user_id,
                        thread_id_val,
                        {
                            "current_discount_percent": result.get("current_discount_percent", 0.0),
                            "combo_offer": result.get("combo_offer", None),
                        },
                    )

                    updated_cart = await self.cart_repo.get_items(req.user_id)
                    return {
                        "type": "proactive_suggestion",
                        "message": ai_reply,
                        "combo_offer": result.get("combo_offer", None),
                        "suggested_products": result.get("suggested_products", []),
                        "cart": updated_cart,
                    }

            except Exception as e:
                logger.exception("Proactive suggestion failed: %s", e)

        return {"success": True}

    async def stream_event(self, req: EventRequest) -> AsyncGenerator[str, None]:
        """
        Streams system/UI event handling via Server-Sent Events (SSE).
        """
        thread_id_val = req.thread_id or str(req.user_id)
        yield f"data: {json.dumps({'type': 'stream_start', 'event': req.event, 'thread_id': thread_id_val})}\n\n"

        res = await self.process_event(req)
        yield f"data: {json.dumps(res)}\n\n"
        yield "data: [DONE]\n\n"


userController = UserController()
user_controller = userController
AgentController = UserController
agentController = userController
