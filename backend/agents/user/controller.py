import re
import json
import asyncio
import logging
from typing import Optional, Dict, Any, List, AsyncGenerator
from fastapi import Request, HTTPException
from langchain_core.messages import HumanMessage
from sqlmodel import select

from agents.user import agent_service
from config.database import db_connection
from User.models import User, UserRole
from User.database import userRepository
from Cart.database import cart_repository
from Chat.models import ChatMessage
from Chat.schemas import ChatRequest, EventRequest
from Chat.database import chat_audit_repo
from Auth.jwt import AuthHandler
from Auth.controller import is_real_user
from utils.text_cleaning import clean_ai_output, StreamingThoughtFilter
from agents.user.graph import deduplicate_cards

logger = logging.getLogger(__name__)


class AgentController:
    """
    Controller for the User AI Chat Agent.
    Orchestrates user-cart synchronization, access token resolution, in-memory LangGraph execution,
    real-time Server-Sent Events (SSE) token streaming with online thought filtering,
    Generative UI card dispatching strictly scoped to the active turn, and non-blocking state queueing.
    """

    def __init__(self, service=None, audit_repo=None, cart_repo=None):
        self.agent_service = service or agent_service
        self.audit_repo = audit_repo or chat_audit_repo
        self.cart_repo = cart_repo or cart_repository

    @staticmethod
    def extract_token_from_request(
        request: Optional[Request] = None, token_param: Optional[str] = None
    ) -> Optional[str]:
        """Extracts Bearer access token from HTTP headers, request parameters, or explicit string."""
        if token_param and str(token_param).strip():
            raw = str(token_param).strip()
            return raw[7:].strip() if raw.lower().startswith("bearer ") else raw

        if request is not None:
            auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
            if auth_header and auth_header.strip():
                raw = auth_header.strip()
                return raw[7:].strip() if raw.lower().startswith("bearer ") else raw
            query_token = request.query_params.get("token") or request.query_params.get("access_token")
            if query_token and query_token.strip():
                return query_token.strip()

        return None

    async def resolve_user_context(
        self,
        user_id: int,
        token: Optional[str] = None,
        request: Optional[Request] = None,
    ) -> Dict[str, Any]:
        """
        Decodes access token if available to resolve the verified user_id and customer profile.
        Falls back to verifying user_id against the database.
        Returns a dict: {"user_id": int, "is_authenticated": bool, "customer_profile": Optional[dict], "token": Optional[str]}
        """
        extracted_token = self.extract_token_from_request(request, token)
        authenticated_user_id = None
        customer_profile = None
        is_authenticated = False

        if extracted_token:
            try:
                decoded = AuthHandler.decode_token(extracted_token)
                if decoded and "user_id" in decoded:
                    authenticated_user_id = int(decoded["user_id"])
                    is_authenticated = True
            except Exception as e:
                logger.debug("Access token decoding failed or expired: %s", e)

        # If token was verified, use its user_id; otherwise use passed user_id
        effective_user_id = authenticated_user_id if authenticated_user_id is not None else user_id

        # Lookup user profile in database
        try:
            db_user = await userRepository.get_by_id(effective_user_id)
            if db_user:
                real_user = is_real_user(db_user)
                if real_user:
                    is_authenticated = True
                customer_profile = {
                    "id": db_user.id,
                    "name": db_user.name,
                    "email": db_user.email,
                    "address": db_user.address,
                    "role": db_user.role.value if hasattr(db_user.role, "value") else str(db_user.role),
                }
        except Exception as db_err:
            logger.warning("Could not load user profile for user_id=%s: %s", effective_user_id, db_err)

        return {
            "user_id": effective_user_id,
            "is_authenticated": is_authenticated,
            "customer_profile": customer_profile,
            "token": extracted_token,
        }

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

    async def _prepare_initial_state(
        self,
        user_id: int,
        thread_id_val: str,
        human_msg: HumanMessage,
        token: Optional[str] = None,
        request: Optional[Request] = None,
    ):
        """
        Hydrates cached conversation summary and customer identity from access token, DB, and Redis.
        Initializes turn-scoped cards and suggested products to empty arrays.
        """
        user_ctx = await self.resolve_user_context(user_id=user_id, token=token, request=request)
        eff_user_id = user_ctx["user_id"]
        is_authenticated = user_ctx["is_authenticated"]
        customer_profile = user_ctx["customer_profile"]

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
                if not customer_profile and cached_data.get("customer_profile"):
                    customer_profile = cached_data.get("customer_profile")
                if not is_authenticated and cached_data.get("is_authenticated"):
                    is_authenticated = True
                if eff_user_id <= 0 and cached_data.get("user_id"):
                    eff_user_id = int(cached_data.get("user_id"))
        except Exception as cache_err:
            logger.warning("Could not read cached agent state: %s", cache_err)

        initial_state = {
            "messages": [human_msg],
            "user_id": eff_user_id,
            "thread_id": thread_id_val,
            "is_authenticated": is_authenticated,
            "customer_profile": customer_profile,
            "cards": [],
            "suggested_products": [],
        }
        if cached_summary:
            initial_state["conversation_summary"] = cached_summary
        if cached_facts:
            initial_state["important_facts"] = cached_facts

        return initial_state, cached_summary, cached_facts, eff_user_id

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
        cards = deduplicate_cards(list(state.get("cards") or []))

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

        # Reliably persist conversation turn (human + AI message + cards + tools) directly to MongoDB chat audit
        try:
            executed_tools = []
            for msg in state.get("messages", []):
                t_calls = getattr(msg, "tool_calls", None)
                if t_calls:
                    for tc in t_calls:
                        t_name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", str(tc))
                        t_args = tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", {})
                        executed_tools.append({"name": t_name, "args": t_args})

            cart_list = state.get("cart") or state.get("cart_items") or []
            selling_tot = 0.0
            cost_tot = 0.0
            if isinstance(cart_list, list):
                for item in cart_list:
                    if isinstance(item, dict):
                        p_val = float(item.get("price") or 0.0)
                        c_val = float(item.get("cost_price") or 0.0)
                        q_val = int(item.get("quantity") or 1)
                        selling_tot += p_val * q_val
                        cost_tot += c_val * q_val

            final_prof = max(0.0, (selling_tot * (1.0 - current_discount / 100.0)) - cost_tot)

            patch_payload = {
                "current_discount_percent": current_discount,
                "cart_products": cart_list,
                "total_selling_price": round(selling_tot, 2),
                "total_cost_price": round(cost_tot, 2),
                "final_profit": round(final_prof, 2),
                "order_placed": bool(state.get("order_placed") or payment_link),
            }
            if payment_link:
                patch_payload["pending_payment_link"] = payment_link
            if state.get("negotiation_log"):
                patch_payload["negotiation_log"] = state.get("negotiation_log")
            if combo_offer:
                patch_payload["combo_offer"] = combo_offer

            asyncio.create_task(
                self.audit_repo.save_full_thread_turn(
                    user_id=user_id,
                    thread_id=thread_id_val,
                    human_text=getattr(human_msg, "content", str(human_msg)),
                    ai_text=ai_reply,
                    cards=cards,
                    tool_calls=executed_tools,
                    state_patch=patch_payload,
                )
            )
        except Exception as persist_err:
            logger.warning("Could not persist chat thread to Mongo dukaan_audit: %s", persist_err)

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
            "user_id": user_id,
        }

    async def process_message(self, req: ChatRequest, request: Optional[Request] = None) -> dict:
        """
        Fast execution for chat messages without blocking audit database calls.
        Extracts authentication from request headers or body token.
        """
        token = getattr(req, "access_token", None)
        thread_id_val = req.thread_id or str(req.user_id)
        config = {"configurable": {"thread_id": thread_id_val}}
        human_msg = HumanMessage(content=req.text)

        initial_state, cached_summary, cached_facts, eff_user_id = await self._prepare_initial_state(
            req.user_id, thread_id_val, human_msg, token=token, request=request
        )
        req.user_id = eff_user_id

        try:
            await self.sync_cart_and_user(eff_user_id, req.cart)
        except Exception as e:
            logger.warning("sync_cart_and_user failed during process_message: %s", e)

        try:
            # Directly invoke LangGraph conversation agent without pre-call database blocking
            agent = await self.agent_service.get_agent_async()
            result = await agent.ainvoke(initial_state, config=config)

            return await self._post_process_chat_completion(
                eff_user_id, thread_id_val, result, cached_summary, cached_facts, human_msg
            )

        except Exception as e:
            logger.exception("Chat agent failed in process_message: %s", e)
            return {
                "type": "chat_reply",
                "message": "Sorry, something went wrong. Please try again!",
                "cards": [],
                "suggested_products": [],
            }

    async def stream_message(
        self, req: ChatRequest, request: Optional[Request] = None
    ) -> AsyncGenerator[str, None]:
        """
        Streams LangGraph execution tokens in REAL TIME as they are produced by the LLM.
        Applies StreamingThoughtFilter to strip internal <think>, <thought>, and <reasoning> tags
        so zero internal model monologue leaks into the UI.
        Emits graph node updates, intermediate tool state, real-time tokens, Generative UI cards, and final payload.
        """
        token = getattr(req, "access_token", None)
        thread_id_val = req.thread_id or str(req.user_id)
        config = {"configurable": {"thread_id": thread_id_val}}
        human_msg = HumanMessage(content=req.text)

        initial_state, cached_summary, cached_facts, eff_user_id = await self._prepare_initial_state(
            req.user_id, thread_id_val, human_msg, token=token, request=request
        )
        req.user_id = eff_user_id

        try:
            await self.sync_cart_and_user(eff_user_id, req.cart)
        except Exception as e:
            logger.warning("sync_cart_and_user failed during stream_message: %s", e)

        thought_filter = StreamingThoughtFilter()
        streamed_tokens: List[str] = []

        try:
            # Signal stream initiation immediately
            yield f"data: {json.dumps({'type': 'stream_start', 'thread_id': thread_id_val, 'user_id': eff_user_id})}\n\n"

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
                                for card in deduplicate_cards(output["cards"]):
                                    yield f"data: {json.dumps({'type': 'card', 'card': card})}\n\n"

            # Flush any remaining clean buffer from thought filter
            flushed = thought_filter.flush()
            if flushed:
                streamed_tokens.append(flushed)
                yield f"data: {json.dumps({'type': 'token', 'content': flushed})}\n\n"

            # Final response assembly and non-blocking background queue persistence
            final_payload = await self._post_process_chat_completion(
                eff_user_id, thread_id_val, latest_state, cached_summary, cached_facts, human_msg
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

    async def process_event(self, req: EventRequest, request: Optional[Request] = None) -> dict:
        """
        Fast execution for system/UI triggered events.
        """
        token = getattr(req, "access_token", None)
        user_ctx = await self.resolve_user_context(user_id=req.user_id, token=token, request=request)
        eff_user_id = user_ctx["user_id"]
        req.user_id = eff_user_id

        thread_id_val = req.thread_id or str(eff_user_id)
        config = {"configurable": {"thread_id": thread_id_val}}

        # Event 0: Authentication Sync Event (login or signup)
        if req.event in ["login", "signup", "user_login", "user_signup", "auth_sync"]:
            sync_res = await self.sync_auth_state(
                thread_id=thread_id_val,
                user_id=eff_user_id,
                token=token or user_ctx.get("token"),
                customer_profile=user_ctx.get("customer_profile"),
                request=request,
            )
            cart_items = []
            try:
                cart_items = await self.cart_repo.get_items(eff_user_id)
            except Exception:
                pass

            return {
                "type": "chat_reply",
                "message": sync_res.get("message"),
                "cards": [],
                "suggested_products": [],
                "user_id": eff_user_id,
                "is_authenticated": True,
                "customer_profile": sync_res.get("customer_profile"),
                "cart": cart_items,
            }

        # Event 1: Combo Declined
        if req.event == "combo_declined":
            try:
                agent = await self.agent_service.get_agent_async()
                try:
                    await agent.aupdate_state(config, {"combo_offer": None, "cards": []}, as_node="agent")
                except Exception:
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
                        "user_id": eff_user_id,
                        "thread_id": thread_id_val,
                        "cards": [],
                        "suggested_products": [],
                    },
                    config=config,
                )

                ai_reply = result.get("final_response")
                updated_cart = result.get("cart") or await self.cart_repo.get_items(eff_user_id)
                cards = deduplicate_cards(list(result.get("cards") or []))

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
                    "cards": deduplicate_cards(cards),
                    "combo_offer": result.get("combo_offer", None),
                    "suggested_products": [],
                    "cart": updated_cart,
                    "ai_discount": result.get("current_discount_percent", 0.0),
                    "user_id": eff_user_id,
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
                await self.sync_cart_and_user(eff_user_id, req.cart)
            except Exception as e:
                logger.warning("sync_cart_and_user failed during proactive event: %s", e)

            hidden_msg = HumanMessage(content="PROACTIVE_SUGGESTION_TRIGGER")
            try:
                agent = await self.agent_service.get_agent_async()
                result = await agent.ainvoke(
                    {
                        "messages": [hidden_msg],
                        "user_id": eff_user_id,
                        "thread_id": thread_id_val,
                        "cards": [],
                        "suggested_products": [],
                    },
                    config=config,
                )

                ai_reply = result.get("final_response")
                if ai_reply:
                    updated_cart = result.get("cart") or await self.cart_repo.get_items(eff_user_id)
                    cards = deduplicate_cards(list(result.get("cards") or []))
                    has_rec = any(c.get("type") == "recommendation" for c in cards)
                    suggested = result.get("suggested_products", []) if has_rec else []
                    return {
                        "type": "proactive_suggestion",
                        "message": ai_reply,
                        "cards": cards,
                        "combo_offer": result.get("combo_offer", None),
                        "suggested_products": suggested,
                        "cart": updated_cart,
                        "user_id": eff_user_id,
                    }

            except Exception as e:
                logger.exception("Proactive suggestion failed: %s", e)

        return {"success": True}

    async def stream_event(
        self, req: EventRequest, request: Optional[Request] = None
    ) -> AsyncGenerator[str, None]:
        """
        Streams system/UI event handling via Server-Sent Events (SSE).
        """
        thread_id_val = req.thread_id or str(req.user_id)
        yield f"data: {json.dumps({'type': 'stream_start', 'event': req.event, 'thread_id': thread_id_val})}\n\n"

        res = await self.process_event(req, request=request)
        yield f"data: {json.dumps(res)}\n\n"
        yield "data: [DONE]\n\n"

    async def sync_auth_state(
        self,
        thread_id: Optional[str],
        user_id: Optional[int] = None,
        token: Optional[str] = None,
        customer_profile: Optional[dict] = None,
        request: Optional[Request] = None,
    ) -> dict:
        """
        Directly injects the authenticated user ID and customer profile into the LangGraph AgentState,
        Redis cache, and chat database for the specified thread_id after processing the access token.
        """
        user_ctx = await self.resolve_user_context(
            user_id=user_id or 0,
            token=token,
            request=request,
        )
        eff_user_id = user_ctx["user_id"]
        is_authenticated = user_ctx["is_authenticated"]
        profile = customer_profile or user_ctx["customer_profile"]
        auth_token = user_ctx["token"]

        thread_id_val = thread_id or str(eff_user_id)
        config = {"configurable": {"thread_id": thread_id_val}}

        updates = {
            "user_id": eff_user_id,
            "is_authenticated": is_authenticated,
            "customer_profile": profile,
        }
        if auth_token:
            updates["auth_token"] = auth_token

        # 1. Update LangGraph state for active conversation thread
        try:
            agent = await self.agent_service.get_agent_async()
            try:
                await agent.aupdate_state(config, updates, as_node="agent")
            except Exception:
                await agent.aupdate_state(config, updates)
            logger.info("LangGraph agent state updated for thread %s: user_id=%s", thread_id_val, eff_user_id)
        except Exception as lg_err:
            logger.warning("aupdate_state in sync_auth_state warning: %s", lg_err)

        # 2. Update Redis cached state
        try:
            from config.redis import redisClient
            r_client = redisClient.get_redis_client()
            cache_key = f"agent_state:{thread_id_val}"
            raw = r_client.get(cache_key)
            state_data = json.loads(raw) if raw else {}
            state_data.update(updates)
            r_client.set(cache_key, json.dumps(state_data), ex=86400)
            logger.info("Synced authenticated user %s with agent thread %s in Redis", eff_user_id, thread_id_val)
        except Exception as r_err:
            logger.warning("Redis sync_auth_state warning for thread %s: %s", thread_id_val, r_err)

        # 3. Ensure user exists in cart repository and SQL
        try:
            await self.cart_repo.ensure_user_cart(eff_user_id)
        except Exception:
            pass

        client_name = profile.get("name") if profile else None
        greeting = (
            f"Welcome back, {client_name}! You're logged in and your shopping bag is synced."
            if client_name
            else "You're now logged in! How can I help you today?"
        )

        return {
            "success": True,
            "user_id": eff_user_id,
            "thread_id": thread_id_val,
            "is_authenticated": is_authenticated,
            "customer_profile": profile,
            "message": greeting,
        }


agentController = AgentController()
agent_controller = agentController

userController = agentController
UserController = AgentController
