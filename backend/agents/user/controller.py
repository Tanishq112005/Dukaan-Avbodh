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
from utils.text_cleaning import clean_ai_output, StreamingThoughtFilter

logger = logging.getLogger(__name__)


class AgentController:
    """
    Controller for the User AI Chat Agent.
    Orchestrates user-cart synchronization, in-memory LangGraph execution,
    real-time Server-Sent Events (SSE) token streaming with online thought filtering,
    Generative UI card dispatching strictly scoped to the active turn, and non-blocking state queueing.
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
        Initializes turn-scoped cards and suggested products to empty arrays.
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
            "cards": [],
            "suggested_products": [],
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
        Extracts final AI reply, packages turn-scoped UI cards,
        and dispatches state to the background queue asynchronously without blocking the user response.
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
        cards = list(state.get("cards") or [])

        # Strictly scope suggested_products: only return if a recommendation card was produced in THIS turn
        has_rec = any(c.get("type") == "recommendation" for c in cards)
        raw_suggested = state.get("suggested_products", []) if has_rec else []
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

        # Asynchronously dispatch state to task queue for background summarization and Mongo persistence
        try:
            from task_queue.sendingResult import sendingResult

            raw_msgs = state.get("messages", [])
            all_msgs = [human_msg] + [m for m in raw_msgs if m != human_msg] if raw_msgs and raw_msgs[0] != human_msg else raw_msgs

            queue_payload = {
                "thread_id": thread_id_val,
                "user_id": user_id,
                "messages": all_msgs or [human_msg],
                "conversation_summary": state.get("conversation_summary") or cached_summary or "",
                "important_facts": state.get("important_facts") or cached_facts or {},
                "current_discount_percent": current_discount,
                "combo_offer": combo_offer,
                "final_response": ai_reply,
            }
            # Fire-and-forget background queue dispatch (zero latency overhead on HTTP response)
            asyncio.create_task(sendingResult.sendData(queue_payload))
        except Exception as q_err:
            logger.warning("Failed to dispatch chat state to background queue: %s", q_err)

        # Use updated cart directly from state if populated by tools, avoiding redundant SQL query
        updated_cart = state.get("cart") or state.get("cart_items")
        if updated_cart is None:
            try:
                updated_cart = await self.cart_repo.get_items(user_id)
            except Exception:
                updated_cart = []

        return {
            "type": "chat_reply",
            "message": ai_reply,
            "cards": cards,
            "combo_offer": combo_offer,
            "suggested_products": suggested_products,
            "cart": updated_cart,
            "ai_discount": current_discount,
            "payment_link": payment_link,
            "payment_link_id": payment_link_id,
        }

    async def process_message(self, req: ChatRequest) -> dict:
        """
        Fast execution for chat messages without blocking audit database calls.
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
            # Directly invoke LangGraph conversation agent without pre-call database blocking
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
                "cards": [],
                "suggested_products": [],
            }

    async def stream_message(self, req: ChatRequest) -> AsyncGenerator[str, None]:
        """
        Streams LangGraph execution tokens in REAL TIME as they are produced by the LLM.
        Applies StreamingThoughtFilter to strip internal <think>, <thought>, and <reasoning> tags
        so zero internal model monologue leaks into the UI.
        Emits graph node updates, intermediate tool state, real-time tokens, Generative UI cards, and final payload.
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

        thought_filter = StreamingThoughtFilter()
        streamed_tokens: List[str] = []

        try:
            # Signal stream initiation immediately
            yield f"data: {json.dumps({'type': 'stream_start', 'thread_id': thread_id_val})}\n\n"

            agent = await self.agent_service.get_agent_async()
            latest_state = dict(initial_state)

            # Stream LLM tokens and graph execution in real-time
            async for event in agent.astream_events(initial_state, config=config, version="v2"):
                kind = event.get("event", "")

                # 1. Real-time streaming LLM tokens
                if kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk:
                        # Skip tool call chunks (do not stream tool arguments as chat text)
                        tool_chunks = getattr(chunk, "tool_call_chunks", None)
                        if not tool_chunks:
                            content = getattr(chunk, "content", "")
                            if isinstance(content, str) and content:
                                clean_token = thought_filter.process(content)
                                if clean_token:
                                    streamed_tokens.append(clean_token)
                                    yield f"data: {json.dumps({'type': 'token', 'content': clean_token})}\n\n"

                # 2. Graph node transition updates
                elif kind == "on_chain_start":
                    node_name = event.get("metadata", {}).get("langgraph_node")
                    if node_name:
                        yield f"data: {json.dumps({'type': 'node_update', 'node': node_name})}\n\n"

                # 3. Intermediate tool outputs, cards, and final chain updates
                elif kind == "on_chain_end":
                    node_name = event.get("metadata", {}).get("langgraph_node")
                    output = event.get("data", {}).get("output")
                    if isinstance(output, dict):
                        latest_state.update(output)
                        # When tools finish, stream intermediate tool updates to UI
                        if node_name == "tools":
                            tools_payload = {"type": "node_update", "node": "tools"}
                            for key in (
                                "suggested_products",
                                "current_discount_percent",
                                "cart_total",
                                "cart",
                                "combo_offer",
                                "cards",
                            ):
                                if key in output:
                                    tools_payload[key] = output[key]
                            yield f"data: {json.dumps(tools_payload)}\n\n"

                            # Stream any interactive UI cards produced by the tools immediately
                            if "cards" in output and isinstance(output["cards"], list):
                                for card in output["cards"]:
                                    yield f"data: {json.dumps({'type': 'card', 'card': card})}\n\n"

            # Flush any remaining clean buffer from thought filter
            flushed = thought_filter.flush()
            if flushed:
                streamed_tokens.append(flushed)
                yield f"data: {json.dumps({'type': 'token', 'content': flushed})}\n\n"

            # Final response assembly and non-blocking background queue persistence
            final_payload = await self._post_process_chat_completion(
                req.user_id, thread_id_val, latest_state, cached_summary, cached_facts, human_msg
            )

            # If the LLM provider did not support token streaming, stream words as fallback
            if not streamed_tokens and final_payload.get("message"):
                fallback_text = final_payload["message"]
                words = re.split(r"(\s+)", fallback_text)
                for w in words:
                    if w:
                        yield f"data: {json.dumps({'type': 'token', 'content': w})}\n\n"
                        await asyncio.sleep(0.005)
            elif streamed_tokens:
                # Ensure final payload text matches the streamed text
                combined_text = "".join(streamed_tokens).strip()
                if combined_text:
                    final_payload["message"] = clean_ai_output(combined_text)

            # Complete payload and termination marker
            yield f"data: {json.dumps(final_payload)}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.exception("Error during stream_message: %s", e)
            error_payload = {
                "type": "chat_reply",
                "message": "Sorry, something went wrong while processing your request.",
                "cards": [],
                "suggested_products": [],
                "error": str(e),
            }
            yield f"data: {json.dumps(error_payload)}\n\n"
            yield "data: [DONE]\n\n"

    async def process_event(self, req: EventRequest) -> dict:
        """
        Fast execution for system/UI triggered events.
        """
        thread_id_val = req.thread_id or str(req.user_id)
        config = {"configurable": {"thread_id": thread_id_val}}

        # Event 1: Combo Declined
        if req.event == "combo_declined":
            try:
                agent = await self.agent_service.get_agent_async()
                await agent.aupdate_state(config, {"combo_offer": None, "cards": []})
            except Exception as e:
                logger.warning("combo_declined langgraph update failed: %s", e)

            return {"type": "combo_cleared", "combo_offer": None, "cards": []}

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
                        "cards": [],
                        "suggested_products": [],
                    },
                    config=config,
                )

                ai_reply = result.get("final_response")
                updated_cart = result.get("cart") or await self.cart_repo.get_items(req.user_id)
                cards = list(result.get("cards") or [])

                if result.get("payment_confirmed"):
                    cards.append({
                        "id": f"card_ord_{result.get('pending_payment_link_id', 'confirmed')}",
                        "type": "order_confirmed",
                        "data": {
                            "title": "Order Placed Successfully",
                            "paid": True,
                            "order_id": result.get("pending_payment_link_id") or "CONFIRMED",
                            "delivery_estimate": "3-5 Business Days",
                            "status": "confirmed",
                        },
                    })

                return {
                    "type": "chat_reply",
                    "message": ai_reply or "Checking your payment now...",
                    "cards": cards,
                    "combo_offer": result.get("combo_offer", None),
                    "suggested_products": [],
                    "cart": updated_cart,
                    "ai_discount": result.get("current_discount_percent", 0.0),
                }
            except Exception as e:
                logger.exception("payment_completed event failed: %s", e)
                return {"success": False, "error": "Could not verify payment yet.", "cards": []}

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
                agent = await self.agent_service.get_agent_async()
                result = await agent.ainvoke(
                    {
                        "messages": [hidden_msg],
                        "user_id": req.user_id,
                        "thread_id": thread_id_val,
                        "cards": [],
                        "suggested_products": [],
                    },
                    config=config,
                )

                ai_reply = result.get("final_response")
                if ai_reply:
                    updated_cart = result.get("cart") or await self.cart_repo.get_items(req.user_id)
                    cards = list(result.get("cards") or [])
                    has_rec = any(c.get("type") == "recommendation" for c in cards)
                    suggested = result.get("suggested_products", []) if has_rec else []
                    return {
                        "type": "proactive_suggestion",
                        "message": ai_reply,
                        "cards": cards,
                        "combo_offer": result.get("combo_offer", None),
                        "suggested_products": suggested,
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


agentController = AgentController()
agent_controller = agentController

userController = agentController
UserController = AgentController
