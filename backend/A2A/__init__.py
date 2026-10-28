"""
Backward-compatibility alias for the unified `agents.a2a` module.
"""

from agents.a2a import *
from agents.a2a.routes import router
from agents.a2a.controller import a2a_controller, A2AController
from agents.a2a.service import a2a_service, A2AService
from agents.a2a.schemas import (
    A2AStartSessionResponse,
    A2AInteractRequest,
    A2AInteractResponse,
    A2AAgentCard,
    A2ACatalogItem,
    A2ACatalogResponse,
)

__all__ = [
    "A2AService",
    "a2a_service",
    "A2AController",
    "a2a_controller",
    "router",
    "A2AStartSessionResponse",
    "A2AInteractRequest",
    "A2AInteractResponse",
    "A2AAgentCard",
    "A2ACatalogItem",
    "A2ACatalogResponse",
]
