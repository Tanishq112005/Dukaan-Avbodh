# mcp/user.py
from mcp.server import mcp
from repositories import UserRepository

user_repo = UserRepository()


@mcp.tool()
async def register_buyer(name: str, agent_type: str, identifier: str) -> dict:
    """Buyer/AI agent ko register/lookup karta hai."""
    user = await user_repo.get_or_create(name=name, agent_type=agent_type, identifier=identifier)
    return user.model_dump()