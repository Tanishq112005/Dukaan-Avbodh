from fastapi import APIRouter, Request
from agents.a2a.controller import a2a_controller
from agents.a2a.schemas import (
    A2AStartSessionResponse,
    A2AInteractRequest,
    A2AInteractResponse,
)

router = APIRouter(tags=["A2A Protocol"])


@router.post("/a2a/start_session", response_model=A2AStartSessionResponse, summary="Start A2A Session")
async def start_session():
    """
    Provisions a new A2A shopping session and returns a chat_token to be used
    in all subsequent agent interactions.
    """
    return await a2a_controller.start_session()


@router.get("/.well-known/agent-card.json", summary="A2A Agent Card Discovery")
async def get_agent_card(request: Request):
    """
    Returns the Agent Card (identity, skills, and endpoints) for discovery
    by external buyer agents and the standard A2A Inspector.
    """
    return await a2a_controller.get_agent_card(request=request)


@router.get("/a2a/catalog", summary="A2A Product Catalog")
async def get_catalog():
    """
    Returns a machine-readable catalog of products available in the Dukaan store.
    """
    return await a2a_controller.get_catalog()


@router.post("/a2a/interact", response_model=A2AInteractResponse, summary="A2A Direct REST Interaction")
async def interact(payload: A2AInteractRequest):
    """
    Direct REST interaction endpoint for buyer agents to query catalog,
    add items to cart, negotiate prices, and checkout.
    """
    return await a2a_controller.interact(payload=payload)


@router.post("/a2a/interact/message:send", summary="A2A JSON-RPC Message Send")
async def a2a_interact_jsonrpc(request: Request):
    """
    Standard A2A JSON-RPC 2.0 endpoint for receiving messages from external agents
    and A2A inspector clients.
    """
    return await a2a_controller.handle_jsonrpc_message(request=request)
