import asyncio
import os
import sys

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from Auth.tools import request_login
from agents.user.graph import _build_cards_from_tool


async def run_auth_card_tests():
    print("=" * 60)
    print("TESTING AUTH PROMPT CARD GENERATION AND INTEGRATION")
    print("=" * 60)

    # 1. Test request_login tool output
    res = await request_login(action_reason="save items to your cart and track orders")
    print("\n[1] request_login tool output:")
    print(res)

    assert res["success"] is True
    assert res["action"] == "request_login"
    assert res["requires_login"] is True
    assert res["login_url"] == "/login"
    assert res["signup_url"] == "/signup"
    assert "save items to your cart" in res["message"]
    assert len(res["benefits"]) >= 3

    # 2. Test _build_cards_from_tool with request_login tool
    cards = _build_cards_from_tool(
        tool_name="request_login",
        parsed=res,
        updates={},
        state={"user_id": 0},
    )
    print("\n[2] Cards generated from request_login:")
    print(cards)

    assert len(cards) == 1, "Should generate exactly 1 card"
    auth_card = cards[0]
    assert auth_card["type"] == "auth_prompt"
    assert auth_card["data"]["title"] == "Sign In to Dukaan"
    assert auth_card["data"]["login_url"] == "/login"
    assert auth_card["data"]["signup_url"] == "/signup"
    assert len(auth_card["data"]["benefits"]) >= 3
    print("  -> Auth prompt card successfully generated with /login and /signup buttons!")

    # 3. Test _build_cards_from_tool with any tool that returns requires_login: True
    cart_guest_error = {
        "success": False,
        "requires_login": True,
        "action": "request_login",
        "message": "Please sign in to add items to your cart.",
        "action_reason": "add items to cart",
    }
    cards_from_cart = _build_cards_from_tool(
        tool_name="add_to_cart",
        parsed=cart_guest_error,
        updates={},
        state={"user_id": 0},
    )
    print("\n[3] Cards generated from guest cart addition failure:")
    print(cards_from_cart)

    assert len(cards_from_cart) == 1
    assert cards_from_cart[0]["type"] == "auth_prompt"
    assert cards_from_cart[0]["data"]["login_url"] == "/login"
    assert cards_from_cart[0]["data"]["signup_url"] == "/signup"
    print("  -> Guest cart failure seamlessly converted to auth_prompt card!")

    print("\n" + "=" * 60)
    print("ALL AUTH PROMPT CARD TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_auth_card_tests())
