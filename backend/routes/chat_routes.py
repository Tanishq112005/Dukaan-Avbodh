"""
Legacy router alias.
Centralized user agent routing is now located in agents.user.routes and agents.user.controller.
"""
from agents.user.routes import (
    router,
    chat_message_endpoint as chat_message,
    chat_event_endpoint as chat_event,
)
from agents.user.controller import userController, UserController

__all__ = ["router", "chat_message", "chat_event", "userController", "UserController"]
