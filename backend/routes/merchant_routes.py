"""
Merchant routes module.
Forwards to the unified Merchant domain routes in `Merchant.routes`.
Preserves backward compatibility for main.py imports.
"""
from Merchant.routes import router, get_analytics, get_all_orders, get_audit_logs, get_all_chat_threads, chat_with_merchant_agent
from Merchant.schemas import MerchantChatRequest

__all__ = [
    "router",
    "get_analytics",
    "get_all_orders",
    "get_audit_logs",
    "get_all_chat_threads",
    "chat_with_merchant_agent",
    "MerchantChatRequest",
]
