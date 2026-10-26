import sys
import os
import logging
from typing import Optional, Dict, Any, List
from fastapi import HTTPException
from langchain_core.tools import StructuredTool

# Ensure backend/mcp directory is discoverable for importing FastMCP user server
mcp_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp"))
if mcp_path not in sys.path:
    sys.path.insert(0, mcp_path)

try:
    from mcp_server_user.server import mcp
except Exception:
    class DummyMCP:
        def tool(self, *args, **kwargs):
            return lambda fn: fn
        def resource(self, *args, **kwargs):
            return lambda fn: fn
    mcp = DummyMCP()

from Auth.controller import authController, is_real_user
from Auth.schemas import UpdateProfileRequest
from User.database import userRepository

logger = logging.getLogger(__name__)

LOGIN_NUDGE_MESSAGE = (
    "To save your items across devices, unlock personalized AI styling, "
    "and access VIP bargain deals, please [Log In or Sign Up](/login) to Dukaan!"
)


# ==============================================================================
# FastMCP Auth Resources
# ==============================================================================

@mcp.resource("auth://policy")
async def get_auth_policy_resource() -> Dict[str, Any]:
    """
    Returns Dukaan customer authentication, guest session, and account privacy policies.
    """
    return {
        "guest_policy": "Guests can explore the full catalog, get instant recommendations, and build a local cart.",
        "member_benefits": [
            "Permanent shopping cart saved across devices and sessions.",
            "Personalized style recommendations based on sizing and aesthetic history.",
            "Eligibility for interactive AI price bargaining and combo deals.",
            "Fast 1-click checkout with saved delivery addresses.",
            "Order tracking with live fulfillment updates.",
        ],
        "privacy": "Customer contact details and delivery addresses are encrypted and strictly confidential.",
    }


# ==============================================================================
# FastMCP Auth & User Profile Tools
# ==============================================================================

@mcp.tool()
async def get_user_profile(
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Fetches the shopper's account profile, contact details, and saved delivery address.

    Parameters:
    - user_id (int, Optional): Customer ID to look up.

    LLM Usage & Instructions:
    1. Call this tool BEFORE asking the customer for their delivery details or placing an order.
    2. If a delivery address is already saved, read it back concisely and ask them to confirm it:
       "I see your delivery address is saved as [Address]. Shall we ship your order there?"
    3. If the address is missing or empty, ask the customer for their delivery address.
    """
    if not user_id or user_id <= 0:
        return {
            "success": True,
            "is_authenticated": False,
            "user_id": None,
            "name": None,
            "email": None,
            "address": None,
            "is_complete": False,
            "missing_fields": ["name", "email", "address"],
            "message": "Guest browsing session. No saved address found.",
        }

    try:
        user = await userRepository.get_by_id(user_id)
        if not user:
            return {
                "success": True,
                "is_authenticated": False,
                "user_id": user_id,
                "name": None,
                "email": None,
                "address": None,
                "is_complete": False,
                "missing_fields": ["name", "email", "address"],
            }

        authenticated = is_real_user(user)
        missing = []
        if not user.name or user.name.lower().startswith("guest"):
            missing.append("name")
        if not authenticated or not user.email or user.email.endswith("@dukaan.local"):
            missing.append("email")
        if not user.address or not user.address.strip():
            missing.append("address")

        return {
            "success": True,
            "is_authenticated": authenticated,
            "user_id": user.id,
            "name": user.name if "name" not in missing else None,
            "email": user.email if "email" not in missing else None,
            "address": user.address if "address" not in missing else None,
            "is_complete": len(missing) == 0,
            "missing_fields": missing,
        }

    except Exception as e:
        logger.exception("get_user_profile tool error: %s", e)
        return {
            "success": False,
            "error": f"Failed to retrieve profile: {str(e)}",
        }


@mcp.tool()
async def update_user_profile(
    user_id: Optional[int] = None,
    name: Optional[str] = None,
    email: Optional[str] = None,
    address: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Updates the customer's delivery shipping address, recipient name, or contact email.

    Parameters:
    - user_id (int, Optional): Customer ID to update.
    - name (str, Optional): Full name of the recipient for package delivery.
    - email (str, Optional): Contact email address for order notifications and invoice.
    - address (str, Optional): Complete shipping address (street, city, state, postal code).

    LLM Usage & Instructions:
    1. Call this tool when the customer provides or changes their delivery shipping address or contact info.
    2. Confirm the updated details warmly before proceeding with checkout.
    """
    if not user_id or user_id <= 0:
        return {
            "success": False,
            "error": "A customer user_id is required to update delivery address and profile.",
            "requires_login": True,
        }

    try:
        user = await userRepository.update_profile(
            user_id=user_id,
            name=name.strip() if name else None,
            email=email.strip().lower() if email else None,
            address=address.strip() if address else None,
        )

        if not user:
            # If user record doesn't exist yet, ensure guest exists then update
            await userRepository.ensure_guest_exists(user_id)
            user = await userRepository.update_profile(
                user_id=user_id,
                name=name.strip() if name else None,
                email=email.strip().lower() if email else None,
                address=address.strip() if address else None,
            )

        return {
            "success": True,
            "message": "Shipping and contact details updated successfully.",
            "user_id": user.id if user else user_id,
            "name": user.name if user else name,
            "email": user.email if user else email,
            "address": user.address if user else address,
        }

    except Exception as e:
        logger.exception("update_user_profile tool error: %s", e)
        return {
            "success": False,
            "error": f"Failed to update profile: {str(e)}",
        }


@mcp.tool()
async def check_auth_status(
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Checks whether the current shopper is logged in as an authenticated member or browsing as a guest.

    Parameters:
    - user_id (int, Optional): Customer ID from session.

    LLM Usage & Instructions:
    1. Call this tool when deciding whether the user can access member-only perks (saved cart, VIP discounts).
    2. If is_authenticated is False, gently guide them with the login/signup links.
    """
    try:
        return await authController.check_status(user_id)
    except Exception as e:
        logger.exception("check_auth_status tool error: %s", e)
        return {
            "is_authenticated": False,
            "user_id": user_id,
            "login_url": "/login",
            "signup_url": "/signup",
            "error": str(e),
        }


@mcp.tool()
async def request_login(
    action_reason: str = "save items to your cart across devices and unlock VIP deals",
) -> Dict[str, Any]:
    """
    Generates a conversational authentication nudge providing direct login and registration links
    and automatically renders an interactive card with Log In and Sign Up buttons in the chat UI.

    Parameters:
    - action_reason (str, Optional): Reason why login is recommended (e.g. 'checkout', 'save cart across devices', 'view order history', 'track orders', 'VIP discount').

    LLM Usage & Instructions:
    1. Call this tool when an unauthenticated guest attempts an action that requires a registered account.
    2. Calling this tool automatically displays an interactive card with dedicated 'Log In' (/login) and 'Sign Up' (/signup) buttons.
    3. Share the login link formatted as markdown [Log In or Sign Up](/login) in your conversational response.
    """
    return {
        "success": True,
        "action": "request_login",
        "requires_login": True,
        "title": "Sign In to Dukaan",
        "login_url": "/login",
        "signup_url": "/signup",
        "action_reason": action_reason,
        "reason": f"Please sign in or create an account to {action_reason}.",
        "message": f"To {action_reason}, please sign in or create an account.",
        "benefits": [
            "Sync your shopping bag across all devices",
            "Track live order shipments & delivery updates",
            "Unlock member-exclusive bargaining discounts",
        ],
    }


# ==============================================================================
# LangChain / LangGraph Adapter Helper
# ==============================================================================

def get_auth_langchain_tools() -> List[StructuredTool]:
    """
    Returns authentication and customer profile tools wrapped as native LangChain StructuredTools,
    ready to bind directly to the unified User Agent with zero network overhead.
    """
    return [
        StructuredTool.from_function(
            coroutine=get_user_profile,
            name="get_user_profile",
            description=get_user_profile.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=update_user_profile,
            name="update_user_profile",
            description=update_user_profile.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=check_auth_status,
            name="check_auth_status",
            description=check_auth_status.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=request_login,
            name="request_login",
            description=request_login.__doc__,
        ),
    ]
