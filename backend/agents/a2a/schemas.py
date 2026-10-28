from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Session Management Schemas
# ---------------------------------------------------------------------------

class A2AStartSessionResponse(BaseModel):
    chat_token: str = Field(
        ...,
        description="Unique session token to maintain conversation and cart context across requests."
    )
    message: str = Field(
        ...,
        description="Welcome message and instructions for interacting with Dukaan AI Sales Agent."
    )


# ---------------------------------------------------------------------------
# Direct Interaction Schemas
# ---------------------------------------------------------------------------

class A2AInteractRequest(BaseModel):
    chat_token: str = Field(
        ...,
        description="The session token received from /a2a/start_session."
    )
    intent: str = Field(
        ...,
        description="Natural language intent (e.g. 'search for blue jeans', 'add product 2 to cart', 'negotiate 10% discount', 'checkout')."
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional structured metadata such as sizes, product IDs, quantities, or buyer preferences."
    )


class A2AInteractResponse(BaseModel):
    status: str = Field(
        ...,
        description="Status code: 'success', 'error', 'counter_offer', or 'action_completed'."
    )
    message: str = Field(
        ...,
        description="Natural language response from the Dukaan agent."
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured payload returned (e.g. order details, cart contents, product cards)."
    )
    suggested_products: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional list of recommended products matching the buyer request."
    )


# ---------------------------------------------------------------------------
# Machine-Readable Catalog Schemas
# ---------------------------------------------------------------------------

class A2ACatalogItem(BaseModel):
    product_id: int = Field(..., description="Unique product ID.")
    name: str = Field(..., description="Product title.")
    description: Optional[str] = Field(default=None, description="Detailed product description.")
    price: float = Field(..., description="Selling price in INR.")
    stock: int = Field(..., description="Current stock inventory count.")
    category: Optional[str] = Field(default=None, description="Product category or garment type.")


class A2ACatalogResponse(BaseModel):
    store: str = Field(default="Dukaan", description="Store name.")
    items: List[A2ACatalogItem] = Field(default_factory=list, description="List of available products.")


# ---------------------------------------------------------------------------
# Agent Card Specification Schemas (Standard A2A Protocol)
# ---------------------------------------------------------------------------

class A2AAgentCardSkill(BaseModel):
    id: str
    name: str
    description: str
    tags: List[str] = Field(default_factory=list)
    examples: List[str] = Field(default_factory=list)


class A2AAgentCardInterface(BaseModel):
    url: str
    protocolBinding: str = "HTTP+JSON"
    protocolVersion: str = "1.0"


class A2AAgentCardCapabilities(BaseModel):
    streaming: bool = False
    pushNotifications: bool = False
    extendedAgentCard: bool = False


class A2AAgentCardProvider(BaseModel):
    organization: str = "Dukaan Avbodh"
    url: str = "https://dukaan-avbodh.onrender.com"


class A2AAgentCard(BaseModel):
    name: str = "Dukaan AI Sales Agent"
    description: str = (
        "I am an intelligent sales agent for Dukaan. I can help you search for products, "
        "negotiate prices, build a cart, and execute checkout transactions."
    )
    version: str = "1.0.0"
    supportedInterfaces: List[A2AAgentCardInterface] = Field(default_factory=list)
    capabilities: A2AAgentCardCapabilities = Field(default_factory=A2AAgentCardCapabilities)
    defaultInputModes: List[str] = Field(default_factory=lambda: ["application/json"])
    defaultOutputModes: List[str] = Field(default_factory=lambda: ["application/json"])
    skills: List[A2AAgentCardSkill] = Field(default_factory=list)
    provider: A2AAgentCardProvider = Field(default_factory=A2AAgentCardProvider)
