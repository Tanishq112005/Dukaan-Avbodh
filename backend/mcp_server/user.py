# mcp/user.py
from mcp_server.server import mcp
from repositories import UserRepository

user_repo = UserRepository()


@mcp.tool()
async def register_buyer(name: str, buyer_role: str, identifier: str) -> dict:
    """Ek naya buyer (customer ya agent) register karta hai, taaki baad mein order create kar sake."""
    user = await user_repo.get_or_create(name=name, role=buyer_role, identifier=identifier)
    return {"success": True, "user_id": user.id, "role": user.role}