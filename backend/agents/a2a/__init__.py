"""
A2A (Agent-to-Agent) package.
Provides discovery, catalog publication, session management, and standard A2A JSON-RPC 2.0
and REST protocol interfaces for autonomous buyer agents.
"""

from .service import A2AService, a2a_service
from .controller import A2AController, a2a_controller
from .routes import router
from .schemas import (
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

# Convenient module aliases
service = a2a_service
controller = a2a_controller

__all__ = [
    "A2AService",
    "a2a_service",
    "service",
    "A2AController",
    "a2a_controller",
    "controller",
    "router",
    "A2AStartSessionResponse",
    "A2AInteractRequest",
    "A2AInteractResponse",
    "A2AAgentCard",
    "A2AAgentCardInterface",
    "A2AAgentCardCapabilities",
    "A2AAgentCardSkill",
    "A2AAgentCardProvider",
    "A2ACatalogItem",
    "A2ACatalogResponse",
]
