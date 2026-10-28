import logging
from typing import Optional, Dict, Any, List
from fastapi import Request, HTTPException, status

from agents.a2a.service import A2AService, a2a_service
from agents.a2a.schemas import (
    A2AStartSessionResponse,
    A2AInteractRequest,
    A2AInteractResponse,
    A2AAgentCard,
    A2AAgentCardInterface,
    A2AAgentCardCapabilities,
    A2AAgentCardSkill,
    A2AAgentCardProvider,
    A2ACatalogItem,
    A2ACatalogResponse,
)

logger = logging.getLogger(__name__)


class A2AController:
    """
    Controller for Agent-to-Agent (A2A) protocol endpoints.
    Encapsulates session provisioning, discovery Agent Card publication,
    catalog synchronization, direct REST buyer agent interactions, and standard
    A2A JSON-RPC 2.0 message handling.
    """

    def __init__(self, service: Optional[A2AService] = None):
        self.service = service or a2a_service

    async def start_session(self) -> A2AStartSessionResponse:
        """
        Initializes an A2A shopping session and returns the session token.
        """
        try:
            token = await self.service.create_session()
            return A2AStartSessionResponse(
                chat_token=token,
                message="Session started. Please include this chat_token in all /a2a/interact requests."
            )
        except Exception as e:
            logger.exception(f"[A2A CONTROLLER] Failed to start session: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start A2A session: {str(e)}"
            )

    async def get_agent_card(self, request: Optional[Request] = None) -> Dict[str, Any]:
        """
        Returns the Agent Card (identity, skills, supported interfaces) for discovery
        by external agents and A2A inspectors.
        """
        base_url = "https://dukaan-avbodh.onrender.com"
        if request is not None:
            try:
                base_url = str(request.base_url).rstrip("/")
            except Exception:
                pass

        card = A2AAgentCard(
            name="Dukaan AI Sales Agent",
            description=(
                "I am an intelligent sales agent for Dukaan. I can help you search for products, "
                "negotiate prices, build a cart, and execute checkout transactions."
            ),
            version="1.0.0",
            supportedInterfaces=[
                A2AAgentCardInterface(
                    url=f"{base_url}/a2a/interact",
                    protocolBinding="HTTP+JSON",
                    protocolVersion="1.0"
                ),
                A2AAgentCardInterface(
                    url=f"{base_url}/a2a/interact/message:send",
                    protocolBinding="JSON-RPC 2.0",
                    protocolVersion="2.0"
                ),
            ],
            capabilities=A2AAgentCardCapabilities(
                streaming=False,
                pushNotifications=False,
                extendedAgentCard=False
            ),
            defaultInputModes=["application/json"],
            defaultOutputModes=["application/json"],
            skills=[
                A2AAgentCardSkill(
                    id="product-discovery",
                    name="Product Discovery",
                    description="Can search the catalog, filter by category, and provide semantic recommendations.",
                    tags=["search", "catalog", "recommendation"],
                    examples=["Show me blue jeans", "What shirts do you have?"]
                ),
                A2AAgentCardSkill(
                    id="cart-management",
                    name="Cart Management",
                    description="Can maintain a persistent cart state per buyer agent, add, update, and remove items.",
                    tags=["cart", "shopping"],
                    examples=["Add 2 blue jeans to my cart", "View cart"]
                ),
                A2AAgentCardSkill(
                    id="negotiation",
                    name="Dynamic Pricing and Negotiation",
                    description="Can evaluate bulk purchases, calculate combo offers, and negotiate discounts.",
                    tags=["discount", "price", "negotiate"],
                    examples=["Can you give me a 10% discount on these jeans?", "Best offer for 3 shirts?"]
                ),
                A2AAgentCardSkill(
                    id="checkout",
                    name="Checkout and Settlement",
                    description="Can convert a cart into an order and integrate with Razorpay for final payment settlement.",
                    tags=["checkout", "pay", "order"],
                    examples=["I want to checkout now", "Generate payment link"]
                ),
            ],
            provider=A2AAgentCardProvider(
                organization="Dukaan Avbodh",
                url=base_url
            )
        )
        return card.model_dump()

    async def get_catalog(self) -> Dict[str, Any]:
        """
        Machine-readable product catalog for Buyer Agents to know available items and stock.
        """
        try:
            products = await self.service.get_catalog_products()
            items = []
            for p in products:
                cat_val = getattr(p, "type", None)
                if hasattr(cat_val, "value"):
                    cat_val = cat_val.value
                elif cat_val is not None:
                    cat_val = str(cat_val)

                items.append(A2ACatalogItem(
                    product_id=p.id,
                    name=p.name,
                    description=getattr(p, "description", None),
                    price=float(p.price),
                    stock=int(getattr(p, "stock", 0)),
                    category=cat_val
                ).model_dump())

            response = A2ACatalogResponse(store="Dukaan", items=items)
            return response.model_dump()
        except Exception as e:
            logger.exception(f"[A2A CONTROLLER] Failed to retrieve catalog: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve catalog: {str(e)}"
            )

    async def interact(self, payload: A2AInteractRequest) -> A2AInteractResponse:
        """
        Direct REST endpoint for external buyer agents to interact with Dukaan.
        """
        if not payload.chat_token or not payload.chat_token.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="chat_token is required."
            )
        if not payload.intent or not payload.intent.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="intent is required."
            )

        result = await self.service.execute_agent_intent(
            intent=payload.intent,
            chat_token=payload.chat_token,
            context=payload.context
        )

        return A2AInteractResponse(
            status=result.get("status", "success"),
            message=result.get("reply_text", ""),
            data=result.get("data"),
            suggested_products=result.get("suggested_products")
        )

    async def handle_jsonrpc_message(self, request: Request) -> Dict[str, Any]:
        """
        Standard A2A JSON-RPC 2.0 Endpoint (e.g. /a2a/interact/message:send)
        for external agent frameworks and A2A Inspector.
        """
        try:
            body = await request.json()
        except Exception:
            body = {}

        # 1. Extract intent text from parts
        intent = ""
        try:
            message_obj = body.get("params", {}).get("message") or body.get("message", {})
            parts = message_obj.get("parts", [])
            for part in parts:
                if isinstance(part, dict):
                    if "text" in part:
                        intent += part.get("text", "") + " "
                    elif part.get("kind") == "text":
                        intent += part.get("text", "") + " "
                elif isinstance(part, str):
                    intent += part + " "
        except Exception:
            pass

        intent = intent.strip() or "Hello"

        # 2. Extract session context ID (chat_token)
        chat_token = (
            body.get("params", {}).get("metadata", {}).get("context_id")
            or body.get("metadata", {}).get("context_id")
            or "default_a2a_session"
        )

        # 3. Execute through service
        result = await self.service.execute_agent_intent(
            intent=intent,
            chat_token=chat_token
        )

        ai_reply = result.get("reply_text") or "Action completed."

        # 4. Inject markdown recommendations for A2A inspectors if any were returned
        suggested = result.get("suggested_products") or []
        if suggested:
            ai_reply += "\n\n### Recommended Products:\n"
            for p in suggested:
                img_url = p.get("image_url") or "https://via.placeholder.com/150"
                ai_reply += f"\n**{p.get('name')}** - ₹{p.get('price')}\n![{p.get('name')}]({img_url})\n"

        # 5. Return A2A standard protobuf-to-JSON response
        return {
            "message": {
                "role": "ROLE_AGENT",
                "parts": [
                    {
                        "text": ai_reply
                    }
                ]
            }
        }


# Singleton instance
a2a_controller = A2AController()
