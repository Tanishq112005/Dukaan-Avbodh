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
    Compliant with standard A2A Inspector format.
    """
    return {
        "name": "Dukaan AI Sales Agent",
        "description": "I am an intelligent sales agent for Dukaan. I can help you search for products, negotiate prices, build a cart, and execute checkout transactions.",
        "version": "1.0.0",
        "supportedInterfaces": [
            {
                "url": "https://dukaan-avbodh.onrender.com/a2a/interact",
                "protocolBinding": "HTTP+JSON",
                "protocolVersion": "1.0"
            }
        ],
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
            "extendedAgentCard": False
        },
        "defaultInputModes": ["application/json"],
        "defaultOutputModes": ["application/json"],
        "skills": [
            {
                "id": "product-discovery",
                "name": "Product Discovery",
                "description": "Can search the catalog, filter by category, and provide semantic recommendations.",
                "tags": ["search", "catalog", "recommendation"],
                "examples": ["Show me blue jeans", "What shirts do you have?"]
            },
            {
                "id": "cart-management",
                "name": "Cart Management",
                "description": "Can maintain a persistent cart state per buyer agent, add, update, and remove items.",
                "tags": ["cart", "shopping"],
                "examples": ["Add 2 blue jeans to my cart"]
            },
            {
                "id": "negotiation",
                "name": "Dynamic Pricing and Negotiation",
                "description": "Can evaluate bulk purchases, calculate combo offers, and negotiate discounts.",
                "tags": ["discount", "price", "negotiate"],
                "examples": ["Can you give me a discount?"]
            },
            {
                "id": "checkout",
                "name": "Checkout and Settlement",
                "description": "Can convert a cart into an order and integrate with Razorpay for final payment settlement.",
                "tags": ["checkout", "pay", "order"],
                "examples": ["I want to checkout now"]
            }
        ],
        "provider": {
            "organization": "Dukaan Avbodh",
            "url": "https://dukaan-avbodh.onrender.com"
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

from fastapi import Request

@router.post("/a2a/interact/message:send")
async def a2a_interact_jsonrpc(req: Request):
    """
    Standard A2A JSON-RPC 2.0 Endpoint for receiving messages from other agents/inspectors.
    """
    body = await req.json()
    
    # Extract intent from A2A schema
    intent = ""
    try:
        parts = body.get("params", {}).get("message", {}).get("parts", [])
        for part in parts:
            if part.get("kind") == "text":
                intent += part.get("text", "") + " "
    except Exception:
        pass
        
    intent = intent.strip() or "Hello"
    
    # Extract session ID (chat_token) from metadata or use a default one
    chat_token = body.get("params", {}).get("metadata", {}).get("context_id", "default_a2a_session")
    
    # Call our agent
    agent = agent_service.get_agent()
    a2a_user_id = await get_or_create_a2a_user(chat_token)
    config = {"configurable": {"thread_id": chat_token}}
    
    prompt = f"[A2A EXTERNAL REQUEST] Intent: {intent}"
    
    try:
        result = await agent.ainvoke({
            "messages": [HumanMessage(content=prompt)],
            "user_id": a2a_user_id
        }, config=config)
        
        ai_reply = result.get("final_response", "Action completed.")
        
    except Exception as e:
        ai_reply = f"Error processing request: {str(e)}"
        
    # Construct A2A standard protobuf-to-JSON response (lf.a2a.v1.SendMessageResponse)
    return {
        "message": {
            "role": "agent",
            "parts": [
                {
                    "kind": "text",
                    "text": ai_reply
                }
            ]
        }
    }
