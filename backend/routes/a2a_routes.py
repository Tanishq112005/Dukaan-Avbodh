import json
import uuid
from fastapi import APIRouter
from schemas.a2a_schemas import A2AInteractRequest, A2AInteractResponse, A2AStartSessionResponse
from agents import agent_service
from langchain_core.messages import HumanMessage
from repositories import ProductRepository

from config.database import db_connection
from models.user import User, UserRole
from sqlmodel import select

router = APIRouter(tags=["A2A Protocol"])
product_repo = ProductRepository()

@router.post("/a2a/start_session", response_model=A2AStartSessionResponse)
async def start_session():
    """
    Initializes a new session for a Buyer Agent. 
    The Buyer Agent MUST call this first to get a chat_token.
    """
    token = f"a2a_{uuid.uuid4().hex[:12]}"
    # We pre-create the user in the database so the session is established
    async with db_connection.get_session() as session:
        user = User(
            name=f"Guest_{token[-4:]}",
            role=UserRole.AI_AGENT,
            identifier=token
        )
        session.add(user)
        await session.commit()
        
    return A2AStartSessionResponse(
        chat_token=token,
        message="Session started. Please include this chat_token in all /a2a/interact requests."
    )

async def get_or_create_a2a_user(chat_token: str) -> int:
    """
    Finds or creates a real database User for the incoming Buyer Agent.
    """
    async with db_connection.get_session() as session:
        result = await session.exec(select(User).where(User.identifier == chat_token))
        user = result.first()
        
        if not user:
            # Create a new Agent User profile in our DB if it somehow doesn't exist
            user = User(
                name=f"Agent {chat_token[-4:]}",
                role=UserRole.AI_AGENT,
                identifier=chat_token
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
        return user.id

@router.get("/.well-known/agent-card.json", summary="A2A Agent Card")
async def get_agent_card():
    """
    Returns the Agent Card (identity and capabilities) for discovery by other agents.
    Compliant with standard A2A discovery patterns (ACP).
    """
    return {
        "schema_version": "1.0",
        "agent_identity": {
            "id": "did:web:dukaan.local:sales_agent",
            "name": "Dukaan AI Sales Agent",
            "role": "Autonomous Merchant Agent",
            "description": "I am an intelligent sales agent for Dukaan. I can help you search for products, negotiate prices, build a cart, and execute checkout transactions."
        },
        "supported_protocols": ["ACP-1.0", "AP2"],
        "capabilities": [
            {
                "name": "product_discovery",
                "description": "Can search the catalog, filter by category, and provide semantic recommendations based on user affinities."
            },
            {
                "name": "cart_management",
                "description": "Can maintain a persistent cart state per buyer agent, add, update, and remove items."
            },
            {
                "name": "dynamic_pricing_and_negotiation",
                "description": "Can evaluate bulk purchases, calculate combo offers, and negotiate discounts bounded by merchant policies."
            },
            {
                "name": "checkout_and_settlement",
                "description": "Can convert a cart into an order and integrate with Razorpay for final payment settlement."
            }
        ],
        "interaction_model": {
            "type": "true_agentic_routing",
            "initialization": {
                "endpoint": "/a2a/start_session",
                "method": "POST",
                "description": "CRITICAL: You MUST call this endpoint first to obtain a chat_token. This token acts as your secure session ID for all subsequent interactions."
            },
            "interaction": {
                "endpoint": "/a2a/interact",
                "method": "POST",
                "request_schema": {
                    "chat_token": "string (required) - The token received from /a2a/start_session",
                    "intent": "string (required) - Natural language instruction of what you want me to do",
                    "context": "object (optional) - Any structured JSON data to help fulfill the intent"
                },
                "response_schema": {
                    "status": "enum: [success, error, counter_offer]",
                    "message": "string - My textual response or negotiation reasoning",
                    "data": "object - Structured data (like order_ids, cart items, prices)"
                },
                "example_flow": [
                    "1. POST /a2a/start_session -> receive { chat_token: '...' }",
                    "2. POST /a2a/interact with { chat_token: '...', intent: 'I want to buy 5 units of product ID 2...' }"
                ]
            }
        },
        "static_endpoints": {
            "catalog": {
                "url": "/a2a/catalog",
                "method": "GET",
                "description": "Fetch the complete machine-readable product catalog without invoking the LLM."
            }
        }
    }

@router.get("/a2a/catalog")
async def get_catalog():
    """
    Machine-readable product catalog for Buyer Agents to know what exists before interacting.
    """
    products = await product_repo.get_all()
    return {
        "store": "Dukaan",
        "items": [
            {
                "product_id": p.id,
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "stock": p.stock,
                "category": p.type.value if hasattr(p.type, 'value') else p.type
            } for p in products
        ]
    }

@router.post("/a2a/interact", response_model=A2AInteractResponse)
async def a2a_interact(req: A2AInteractRequest):
    """
    The True Agentic Endpoint. 
    The Buyer Agent sends its intent, and our LangGraph agent decides which MCP tools to call.
    """
    agent = agent_service.get_agent()
    a2a_user_id = await get_or_create_a2a_user(req.chat_token)
    config = {"configurable": {"thread_id": req.chat_token}}
    
    context_str = json.dumps(req.context) if req.context else "{}"
    
    prompt = f"""
[SYSTEM EVENT: A2A INTERACTION REQUEST]
You are fulfilling a request from an external Buyer Agent (Session Token: {req.chat_token}).
Buyer Agent Intent: "{req.intent}"
Additional Context: {context_str}

Task: Use your tools to fulfill this request (e.g., search_products, add_to_cart, negotiate_discount). 
Reply briefly to confirm what you did.
"""

    try:
        result = await agent.ainvoke({
            "messages": [HumanMessage(content=prompt)],
            "user_id": a2a_user_id
        }, config=config)
        
        ai_reply = result.get("final_response", "Action completed by agent.")
        if not ai_reply:
            ai_reply = "I have processed your request."
            
        # Fetch latest cart state to send back as structured data
        from repositories.cart_repository import cart_repository
        cart_items = await cart_repository.get_cart_items(a2a_user_id)
        
        return A2AInteractResponse(
            status="success",
            message=ai_reply,
            data={
                "cart": cart_items,
                "suggested_products": result.get("suggested_products", []),
                "combo_offer": result.get("combo_offer", None)
            }
        )
    except Exception as e:
        print(f"[A2A ERROR] Agent failed: {e}")
        return A2AInteractResponse(
            status="error",
            message="Internal agent error.",
            data={"error_details": str(e)}
        )
