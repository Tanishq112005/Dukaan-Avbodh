"""
Alias module for `agents.a2a`.
"""

from agents.a2a import *
from agents.a2a.routes import router
from agents.a2a.controller import a2a_controller, A2AController
from agents.a2a.service import a2a_service, A2AService

__all__ = [
    "A2AService",
    "a2a_service",
    "A2AController",
    "a2a_controller",
    "router",
]
