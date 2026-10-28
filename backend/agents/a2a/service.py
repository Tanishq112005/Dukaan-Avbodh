import uuid
import logging
from typing import Optional, Dict, Any, List
from sqlmodel import select
from langchain_core.messages import HumanMessage

from config.database import db_connection
from User.models import User, UserRole
from Product.database import ProductRepository
from agents.user import agent_service

logger = logging.getLogger(__name__)


class A2AService:
    """
    Service layer for Agent-to-Agent (A2A) communication and lifecycle management.
    Handles autonomous buyer sessions, user-agent mapping, catalog retrieval,
    and delegation to the Dukaan AI Sales Agent.
    """

    def __init__(self, product_repo: Optional[ProductRepository] = None, user_agent_service=None):
        self.product_repo = product_repo or ProductRepository()
        self.user_agent_service = user_agent_service or agent_service

    async def create_session(self) -> str:
        """
        Provisions a unique session token and associates a guest customer record in the database.
        """
        token = f"a2a_{uuid.uuid4().hex[:12]}"
        email = f"{token}@dukaan.local"
        async with db_connection.get_session() as session:
            user = User(name=f"Guest_{token[-4:]}", role=UserRole.CUSTOMER, email=email)
            session.add(user)
            await session.commit()
        logger.info(f"[A2A SERVICE] Created session {token} for user {email}")
        return token

    async def get_or_create_user(self, chat_token: str) -> int:
        """
        Retrieves existing customer user or creates a new one corresponding to the given chat_token.
        """
        clean_token = str(chat_token).strip() or "default_a2a_session"
        email = f"{clean_token}@dukaan.local"
        async with db_connection.get_session() as session:
            user = (await session.exec(select(User).where(User.email == email))).first()
            if not user:
                user = User(name=f"Agent {clean_token[-4:]}", role=UserRole.CUSTOMER, email=email)
                session.add(user)
                await session.commit()
                await session.refresh(user)
                logger.info(f"[A2A SERVICE] Provisioned new customer record #{user.id} for {clean_token}")
            return user.id

    async def get_catalog_products(self) -> List[Any]:
        """
        Fetches all catalog products from the repository with defensive fallback.
        """
        if hasattr(self.product_repo, "get_all_products"):
            return await self.product_repo.get_all_products()
        elif hasattr(self.product_repo, "get_all"):
            return await self.product_repo.get_all()
        elif hasattr(self.product_repo, "get_list_of_items_in_stock"):
            return await self.product_repo.get_list_of_items_in_stock()
        return []

    async def get_agent(self) -> Any:
        """
        Safely retrieves the compiled user agent.
        """
        if hasattr(self.user_agent_service, "get_agent_async"):
            return await self.user_agent_service.get_agent_async()
        elif hasattr(self.user_agent_service, "get_agent"):
            return self.user_agent_service.get_agent()
        return None

    async def execute_agent_intent(
        self,
        intent: str,
        chat_token: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes an incoming intent from an external buyer agent or inspector through
        the unified Dukaan sales agent graph.
        """
        clean_token = str(chat_token).strip() or "default_a2a_session"
        clean_intent = str(intent).strip() or "Hello"

        agent = await self.get_agent()
        if agent is None:
            logger.error("[A2A SERVICE] Sales agent graph is not initialized.")
            return {
                "status": "error",
                "reply_text": "Sales agent service is currently unavailable. Please try again shortly.",
                "suggested_products": [],
                "data": None,
            }

        a2a_user_id = await self.get_or_create_user(clean_token)
        config = {"configurable": {"thread_id": clean_token}}

        if context:
            prompt = f"[A2A EXTERNAL REQUEST] Intent: {clean_intent} | Context: {context}"
        else:
            prompt = f"[A2A EXTERNAL REQUEST] Intent: {clean_intent}"

        try:
            result = await agent.ainvoke({
                "messages": [HumanMessage(content=prompt)],
                "user_id": a2a_user_id,
            }, config=config)

            ai_reply = result.get("final_response")
            if not ai_reply:
                messages = result.get("messages", [])
                if messages and hasattr(messages[-1], "content"):
                    ai_reply = messages[-1].content
                else:
                    ai_reply = "Action completed."

            suggested = result.get("suggested_products") or []
            cards = result.get("cards") or []

            return {
                "status": "success",
                "reply_text": str(ai_reply),
                "suggested_products": suggested,
                "cards": cards,
                "data": {
                    "thread_id": clean_token,
                    "user_id": a2a_user_id,
                    "suggested_count": len(suggested),
                    "cards_count": len(cards),
                },
                "raw_result": result,
            }

        except Exception as e:
            logger.exception(f"[A2A SERVICE ERROR] Error processing intent '{clean_intent}': {e}")
            return {
                "status": "error",
                "reply_text": f"Error processing request: {str(e)}",
                "suggested_products": [],
                "cards": [],
                "data": None,
            }


# Singleton instance
a2a_service = A2AService()
