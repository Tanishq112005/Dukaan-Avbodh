import sys
import os
import asyncio

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from Auth.agent_auth import agentAuthService, create_agent_access_token
from Auth.jwt import AuthHandler
from Auth.tools import initiate_agent_login, check_agent_login_status, request_login


async def test_agent_auth_service_lifecycle():
    print("[TEST 1] Testing AgentAuthService lifecycle...")
    session = agentAuthService.create_session(agent_name="ChatGPT-Test")
    assert session is not None
    session_id = session["session_id"]
    code = session["code"]
    assert session_id.startswith("agtsess_")
    assert code.startswith("DUK-")
    assert session["status"] == "pending"
    assert "/auth/authorize" in session["auth_url"]

    retrieved = agentAuthService.get_session(session_id)
    assert retrieved is not None
    assert retrieved["status"] == "pending"
    assert retrieved["user_id"] is None

    by_code = agentAuthService.get_session_by_code(code)
    assert by_code is not None
    assert by_code["session_id"] == session_id

    approval = agentAuthService.approve_session(
        session_id=session_id,
        user_id=101,
        user_name="Test Shopper",
        user_email="shopper@example.com",
    )
    assert approval["success"] is True

    approved_session = agentAuthService.get_session(session_id)
    assert approved_session["status"] == "approved"
    assert approved_session["user_id"] == 101
    assert approved_session["user_name"] == "Test Shopper"
    assert approved_session["access_token"] is not None

    decoded = AuthHandler.decode_token(approved_session["access_token"])
    assert decoded["user_id"] == 101
    assert decoded["role"] == "customer"
    print("[PASS] Test 1: Lifecycle passed.")


async def test_agent_auth_mcp_tools():
    print("[TEST 2] Testing FastMCP tools...")
    init_res = await initiate_agent_login(agent_name="Claude-Shopper")
    assert init_res["success"] is True
    session_id = init_res["session_id"]
    code = init_res["verification_code"]
    assert "auth_url" in init_res
    assert session_id is not None

    pending_status = await check_agent_login_status(session_id)
    assert pending_status["success"] is True
    assert pending_status["is_authenticated"] is False
    assert pending_status["status"] == "pending"

    agentAuthService.approve_session(
        session_id=session_id,
        user_id=202,
        user_name="Priya Patel",
        user_email="priya@example.com",
    )

    approved_status = await check_agent_login_status(session_id)
    assert approved_status["success"] is True
    assert approved_status["is_authenticated"] is True
    assert approved_status["user_id"] == 202
    assert approved_status["user_name"] == "Priya Patel"
    assert approved_status["access_token"] is not None
    print("[PASS] Test 2: MCP Tools passed.")


async def test_agent_auth_rejection():
    print("[TEST 3] Testing rejection flow...")
    session = agentAuthService.create_session(agent_name="BargainBot")
    session_id = session["session_id"]

    reject_res = agentAuthService.reject_session(session_id)
    assert reject_res["success"] is True

    status = await check_agent_login_status(session_id)
    assert status["is_authenticated"] is False
    assert status["status"] == "rejected"
    print("[PASS] Test 3: Rejection flow passed.")


async def main():
    await test_agent_auth_service_lifecycle()
    await test_agent_auth_mcp_tools()
    await test_agent_auth_rejection()
    print("\n[ALL TESTS PASSED] 3/3 Agent Authentication tests passed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
