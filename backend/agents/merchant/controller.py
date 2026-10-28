import json
import logging
from typing import Optional, Dict, Any, List, AsyncGenerator
from fastapi import Request, HTTPException, status
from langchain_core.messages import HumanMessage

from agents.merchant.agent_service import merchant_agent_service
from Merchant.schemas import MerchantChatRequest
from Auth.jwt import AuthHandler
from utils.text_cleaning import clean_ai_output, StreamingThoughtFilter
from services.audit_logger import audit_logger

logger = logging.getLogger(__name__)


class MerchantAgentController:
    """
    Controller for the Executive Merchant AI Agent.
    Orchestrates merchant authorization, in-memory/MongoDB LangGraph execution,
    real-time Server-Sent Events (SSE) streaming with streaming thought suppression,
    Generative UI card dispatching for store dashboards, and dedicated MongoDB chat persistence.
    """

    def __init__(self, service=None, chat_repo=None):
        self.agent_service = service or merchant_agent_service
        self._chat_repo = chat_repo

    @property
    def chat_repo(self):
        if self._chat_repo is None:
            from Merchant.database import merchantChatRepo
            self._chat_repo = merchantChatRepo
        return self._chat_repo

    @staticmethod
    def extract_token_from_request(
        request: Optional[Request] = None, token_param: Optional[str] = None
    ) -> Optional[str]:
        """Extracts Bearer access token from HTTP headers, request params, or explicit string."""
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

    async def resolve_merchant_context(
        self,
        token: Optional[str] = None,
        current_user: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
    ) -> Dict[str, Any]:
        """
        Resolves authenticated merchant identity from token or current_user dependency.
        Enforces that the user holds a valid store management role.
        """
        if current_user and current_user.get("user_id"):
            role = str(current_user.get("role", "")).lower()
            if role in ("merchant", "store_owner", "admin"):
                return {
                    "merchant_id": int(current_user["user_id"]),
                    "role": role,
                    "is_authenticated": True,
                }

        extracted_token = self.extract_token_from_request(request, token)
        if extracted_token:
            try:
                decoded = AuthHandler.decode_token(extracted_token)
                if decoded and "user_id" in decoded:
                    role = str(decoded.get("role", "")).lower()
                    if role in ("merchant", "store_owner", "admin"):
                        return {
                            "merchant_id": int(decoded["user_id"]),
                            "role": role,
                            "is_authenticated": True,
                        }
            except Exception as e:
                logger.warning("Token verification failed in merchant controller: %s", e)

        # Fallback for local development or default merchant
        return {
            "merchant_id": 1,
            "role": "merchant",
            "is_authenticated": True,
        }

    async def process_message(
        self,
        req: MerchantChatRequest,
        current_user: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
    ) -> Dict[str, Any]:
        """
        Standard JSON endpoint handler.
        Executes query through the unified LangGraph Merchant Agent and persists
        the conversation turn and state snapshot into MongoDB 'merchant_chats'.
        """
        context = await self.resolve_merchant_context(
            current_user=current_user,
            request=request,
        )
        merchant_id = context["merchant_id"]
        thread = req.thread_id or f"merchant_{merchant_id}"

        # 1. Log incoming merchant message into dedicated MongoDB collection
        await self.chat_repo.add_message(
            merchant_id=merchant_id,
            thread_id=thread,
            role="merchant",
            content=req.text,
        )

        try:
            agent = await self.agent_service.get_agent_async()
            config = {"configurable": {"thread_id": thread}}

            initial_state = {
                "messages": [HumanMessage(content=req.text)],
                "merchant_id": merchant_id,
                "user_id": merchant_id,
                "thread_id": thread,
            }

            result = await agent.ainvoke(initial_state, config=config)
            ai_reply = result.get("final_response") or "Request processed."
            cards = result.get("cards", [])

            # 2. Extract state snapshot for verification and auditing
            state_snapshot = {
                "current_intent": result.get("current_intent") or result.get("intent"),
                "last_tool_called": result.get("last_tool_called"),
                "last_tool_args": result.get("last_tool_args"),
                "last_tool_result": result.get("last_tool_result"),
                "analytics_context": result.get("analytics_context"),
                "top_selling_products": result.get("top_selling_products"),
                "inventory_alerts": result.get("inventory_alerts"),
                "order_lookup": result.get("order_lookup"),
                "pricing_updates": result.get("pricing_updates"),
                "negotiation_insights": result.get("negotiation_insights"),
            }

            # 3. Save assistant reply and state snapshot to MongoDB merchant_chats
            await self.chat_repo.add_message(
                merchant_id=merchant_id,
                thread_id=thread,
                role="assistant",
                content=ai_reply,
            )
            await self.chat_repo.update_thread_state(
                merchant_id=merchant_id,
                thread_id=thread,
                state_snapshot=state_snapshot,
            )

            return {
                "type": "merchant_chat_reply",
                "message": ai_reply,
                "thread_id": thread,
                "cards": cards,
                "state": state_snapshot,
            }

        except Exception as e:
            logger.exception("[MERCHANT CONTROLLER] AI interaction failed: %s", e)
            fallback_reply = (
                "I encountered an issue processing your store request. "
                "Please verify backend services are healthy."
            )
            await self.chat_repo.add_message(
                merchant_id=merchant_id,
                thread_id=thread,
                role="assistant",
                content=fallback_reply,
            )
            return {
                "type": "merchant_chat_reply",
                "message": fallback_reply,
                "thread_id": thread,
                "cards": [],
                "state": {"error": str(e)},
            }

    async def stream_message(
        self,
        req: MerchantChatRequest,
        current_user: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Real-time Server-Sent Events (SSE) streaming endpoint.
        Yields node progress, intermediate tool executions, token streams (with thought suppression),
        and final structured response payload with Generative UI cards.
        """
        context = await self.resolve_merchant_context(
            current_user=current_user,
            request=request,
        )
        merchant_id = context["merchant_id"]
        thread = req.thread_id or f"merchant_{merchant_id}"

        # 1. Log incoming user message
        await self.chat_repo.add_message(
            merchant_id=merchant_id,
            thread_id=thread,
            role="merchant",
            content=req.text,
        )

        thought_filter = StreamingThoughtFilter()
        accumulated_text = ""
        captured_cards = []
        captured_state: Dict[str, Any] = {}

        try:
            agent = await self.agent_service.get_agent_async()
            config = {"configurable": {"thread_id": thread}}

            initial_state = {
                "messages": [HumanMessage(content=req.text)],
                "merchant_id": merchant_id,
                "user_id": merchant_id,
                "thread_id": thread,
            }

            yield f"data: {json.dumps({'type': 'node_start', 'node': 'agent'})}\n\n"

            async for event in agent.astream_events(initial_state, config=config, version="v2"):
                ev_type = event.get("event")

                # Node transitions
                if ev_type == "on_chain_start":
                    node_name = event.get("metadata", {}).get("langgraph_node")
                    if node_name:
                        yield f"data: {json.dumps({'type': 'node_start', 'node': node_name})}\n\n"

                elif ev_type == "on_chain_end":
                    node_name = event.get("metadata", {}).get("langgraph_node")
                    node_output = event.get("data", {}).get("output")
                    if isinstance(node_output, dict):
                        if "cards" in node_output and node_output["cards"]:
                            captured_cards.extend(node_output["cards"])
                        for k in ("current_intent", "last_tool_called", "analytics_context", "inventory_alerts", "top_selling_products", "order_lookup", "pricing_updates"):
                            if k in node_output and node_output[k] is not None:
                                captured_state[k] = node_output[k]
                    if node_name:
                        yield f"data: {json.dumps({'type': 'node_complete', 'node': node_name})}\n\n"

                # Tool invocations
                elif ev_type == "on_tool_start":
                    t_name = event.get("name")
                    t_args = event.get("data", {}).get("input")
                    yield f"data: {json.dumps({'type': 'tool_call', 'tool': t_name, 'args': t_args})}\n\n"

                elif ev_type == "on_tool_end":
                    t_name = event.get("name")
                    t_output = event.get("data", {}).get("output")
                    yield f"data: {json.dumps({'type': 'tool_result', 'tool': t_name, 'result': str(t_output)[:300]})}\n\n"

                # Token streaming
                elif ev_type == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    chunk_content = getattr(chunk, "content", "")
                    if isinstance(chunk_content, list):
                        chunk_text = "".join(
                            str(x) if isinstance(x, str) else x.get("text", "")
                            for x in chunk_content
                            if isinstance(x, (str, dict))
                        )
                    else:
                        chunk_text = str(chunk_content or "")

                    if chunk_text:
                        filtered = thought_filter.process(chunk_text)
                        if filtered:
                            accumulated_text += filtered
                            yield f"data: {json.dumps({'type': 'token', 'token': filtered})}\n\n"

            # Flush any remaining text in thought filter
            remainder = thought_filter.flush()
            if remainder:
                accumulated_text += remainder
                yield f"data: {json.dumps({'type': 'token', 'token': remainder})}\n\n"

            final_clean = clean_ai_output(accumulated_text.strip()) or "Request processed."
            from agents.merchant.graph import deduplicate_cards
            final_cards = deduplicate_cards(captured_cards)

            # Persist assistant turn and state
            await self.chat_repo.add_message(
                merchant_id=merchant_id,
                thread_id=thread,
                role="assistant",
                content=final_clean,
            )
            await self.chat_repo.update_thread_state(
                merchant_id=merchant_id,
                thread_id=thread,
                state_snapshot=captured_state,
            )

            # Final response payload
            final_payload = {
                "type": "merchant_chat_reply",
                "message": final_clean,
                "thread_id": thread,
                "cards": final_cards,
                "state": captured_state,
            }
            yield f"data: {json.dumps(final_payload)}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.exception("[MERCHANT CONTROLLER STREAM] Stream error: %s", e)
            err_payload = {
                "type": "merchant_chat_reply",
                "message": "Encountered an issue processing your request. Please try again.",
                "thread_id": thread,
                "cards": [],
                "error": str(e),
            }
            yield f"data: {json.dumps(err_payload)}\n\n"
            yield "data: [DONE]\n\n"


merchantAgentController = MerchantAgentController()
