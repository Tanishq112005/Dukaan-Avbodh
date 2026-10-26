import asyncio
import os
import sys

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from Auth.jwt import AuthHandler
from agents.user.controller import agentController
from agents.user.prompts import get_user_agent_prompt
from agents.user.agent import UserAgent
from agents.user.state import AgentState
from Chat.schemas import AuthSyncRequest, ChatRequest, EventRequest


async def run_auth_agent_state_tests():
    print("=" * 65)
    print("TESTING AUTH TOKEN PROCESSING AND AGENT STATE USER_ID SYNCHRONIZATION")
    print("=" * 65)

    test_user_id = 999
    test_role = "customer"
    test_thread_id = "test_thread_auth_sync_001"

    # 1. Generate access token
    token = AuthHandler.create_access_token(user_id=test_user_id, role=test_role)
    print("\n[1] Generated access token:")
    print(" ", token[:30] + "...")
    assert token and isinstance(token, str)

    # 2. Test token extraction
    extracted = agentController.extract_token_from_request(token_param=f"Bearer {token}")
    assert extracted == token, "Bearer token prefix should be cleanly stripped"
    print("\n[2] Token extraction from 'Bearer <token>': SUCCESS")

    # 3. Test resolve_user_context with access token
    user_ctx = await agentController.resolve_user_context(
        user_id=12345, # Simulated guest ID from frontend
        token=token,
    )
    print("\n[3] resolve_user_context result:")
    print(" ", user_ctx)
    assert user_ctx["user_id"] == test_user_id, f"Expected {test_user_id}, got {user_ctx['user_id']}"
    assert user_ctx["is_authenticated"] is True, "Token must mark user as authenticated"
    print("  -> Authenticated token successfully overrode guest user_id with verified user_id!")

    # 4. Test sync_auth_state (updates LangGraph AgentState and Redis)
    sync_result = await agentController.sync_auth_state(
        thread_id=test_thread_id,
        user_id=test_user_id,
        token=token,
        customer_profile={
            "id": test_user_id,
            "name": "Alex Morgan",
            "email": "alex@example.com",
            "address": "Bandra West, Mumbai",
            "role": "customer",
        },
    )
    print("\n[4] sync_auth_state result:")
    print(" ", sync_result)
    assert sync_result["success"] is True
    assert sync_result["user_id"] == test_user_id
    assert sync_result["is_authenticated"] is True
    assert sync_result["customer_profile"]["name"] == "Alex Morgan"
    print("  -> AgentState for thread successfully synced with authenticated user_id!")

    # 5. Verify prompt builder injects authenticated user_id and profile
    prompt_text = get_user_agent_prompt(
        user_id=test_user_id,
        gender="men",
        customer_profile={
            "name": "Alex Morgan",
            "email": "alex@example.com",
            "address": "Bandra West, Mumbai",
        },
        is_authenticated=True,
    )
    print("\n[5] Enriched prompt snippet:")
    for line in prompt_text.splitlines():
        if "Active Customer ID" in line or "Customer Name" in line or "Saved Shipping Address" in line:
            print(" ", line)

    assert f"Active Customer ID (user_id in state): {test_user_id} (LOGGED IN & AUTHENTICATED" in prompt_text
    assert "Customer Name: Alex Morgan" in prompt_text
    assert "Saved Shipping Address: Bandra West, Mumbai" in prompt_text
    print("  -> Prompt builder accurately informs AI stylist that customer is logged in with user_id!")

    # 6. Verify unauthenticated/guest prompt still asks to login
    guest_prompt = get_user_agent_prompt(
        user_id=0,
        is_authenticated=False,
    )
    assert "None / 0 (GUEST / NOT LOGGED IN - Unauthenticated" in guest_prompt
    print("\n[6] Guest prompt check: Verified guest is asked to log in.")

    # 7. Test process_event with auth event
    event_req = EventRequest(
        user_id=test_user_id,
        event="login",
        thread_id=test_thread_id,
        access_token=token,
    )
    event_res = await agentController.process_event(event_req)
    print("\n[7] process_event('login') result:")
    print(" ", event_res)
    assert event_res["user_id"] == test_user_id
    assert event_res["is_authenticated"] is True
    print("  -> Auth event in process_event returns active authenticated state!")

    print("\n" + "=" * 65)
    print("ALL AUTH AGENT STATE SYNCHRONIZATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(run_auth_agent_state_tests())
