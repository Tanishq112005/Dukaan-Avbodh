import sys
import os
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app

from agents.a2a import (
    A2AController,
    a2a_controller,
    A2AService,
    a2a_service,
    router,
    A2AStartSessionResponse,
    A2AInteractRequest,
    A2AInteractResponse,
    A2AAgentCard,
    A2ACatalogItem,
    A2ACatalogResponse,
)


class TestA2AServiceAndController(unittest.IsolatedAsyncioTestCase):
    """
    Unit and integration tests for the unified Agent-to-Agent (A2A) module.
    Verifies service, controller, and FastAPI HTTP route behaviors.
    """

    async def asyncSetUp(self):
        self.mock_product_repo = MagicMock()
        self.mock_user_agent_service = MagicMock()
        self.test_service = A2AService(
            product_repo=self.mock_product_repo,
            user_agent_service=self.mock_user_agent_service,
        )
        self.test_controller = A2AController(service=self.test_service)

    async def test_create_session_and_get_user(self):
        """Test session creation and user resolution."""
        with patch.object(self.test_service, "create_session", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = "a2a_testtoken123"
            token = await self.test_service.create_session()
            self.assertEqual(token, "a2a_testtoken123")

        with patch.object(self.test_service, "get_or_create_user", new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = 42
            user_id = await self.test_service.get_or_create_user("a2a_testtoken123")
            self.assertEqual(user_id, 42)

    async def test_controller_start_session(self):
        """Test controller start_session endpoint handler."""
        with patch.object(self.test_service, "create_session", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = "a2a_mocktoken999"
            response = await self.test_controller.start_session()
            self.assertIsInstance(response, A2AStartSessionResponse)
            self.assertEqual(response.chat_token, "a2a_mocktoken999")
            self.assertIn("Session started", response.message)

    async def test_controller_agent_card(self):
        """Test standard A2A agent card generation."""
        card_dict = await self.test_controller.get_agent_card()
        self.assertEqual(card_dict["name"], "Dukaan AI Sales Agent")
        self.assertEqual(card_dict["version"], "1.0.0")
        self.assertTrue(len(card_dict["supportedInterfaces"]) >= 2)
        self.assertTrue(len(card_dict["skills"]) >= 4)

        skill_ids = [s["id"] for s in card_dict["skills"]]
        self.assertIn("product-discovery", skill_ids)
        self.assertIn("cart-management", skill_ids)
        self.assertIn("negotiation", skill_ids)
        self.assertIn("checkout", skill_ids)

    async def test_controller_get_catalog(self):
        """Test machine-readable catalog retrieval and formatting."""
        mock_p1 = MagicMock()
        mock_p1.id = 1
        mock_p1.name = "Classic Blue Jeans"
        mock_p1.description = "Durable denim jeans"
        mock_p1.price = 1499.0
        mock_p1.stock = 25
        mock_p1.type = "PANTS"

        mock_p2 = MagicMock()
        mock_p2.id = 2
        mock_p2.name = "White Linen Shirt"
        mock_p2.description = "Breathable summer shirt"
        mock_p2.price = 1199.0
        mock_p2.stock = 10
        mock_p2.type = "SHIRT"

        self.mock_product_repo.get_all_products = AsyncMock(return_value=[mock_p1, mock_p2])

        catalog = await self.test_controller.get_catalog()
        self.assertEqual(catalog["store"], "Dukaan")
        self.assertEqual(len(catalog["items"]), 2)
        self.assertEqual(catalog["items"][0]["name"], "Classic Blue Jeans")
        self.assertEqual(catalog["items"][0]["price"], 1499.0)
        self.assertEqual(catalog["items"][1]["stock"], 10)

    async def test_controller_interact_success(self):
        """Test direct REST interaction endpoint handler."""
        with patch.object(self.test_service, "execute_agent_intent", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {
                "status": "success",
                "reply_text": "I found 3 great blue jeans for you!",
                "suggested_products": [{"id": 1, "name": "Classic Blue Jeans", "price": 1499.0}],
                "data": {"thread_id": "a2a_session_1"},
            }

            req = A2AInteractRequest(
                chat_token="a2a_session_1",
                intent="Show me blue jeans",
            )
            res = await self.test_controller.interact(req)
            self.assertIsInstance(res, A2AInteractResponse)
            self.assertEqual(res.status, "success")
            self.assertEqual(res.message, "I found 3 great blue jeans for you!")
            self.assertEqual(len(res.suggested_products), 1)

    async def test_controller_jsonrpc_message(self):
        """Test standard A2A JSON-RPC 2.0 message handler."""
        with patch.object(self.test_service, "execute_agent_intent", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {
                "status": "success",
                "reply_text": "Added to cart with 10% discount.",
                "suggested_products": [
                    {"name": "Slim Jeans", "price": 1200, "image_url": "https://img.test/1.jpg"}
                ],
            }

            mock_request = MagicMock()
            mock_request.json = AsyncMock(return_value={
                "params": {
                    "message": {
                        "parts": [{"text": "Can I negotiate a 10% discount?"}]
                    },
                    "metadata": {
                        "context_id": "a2a_buyer_456"
                    }
                }
            })

            response = await self.test_controller.handle_jsonrpc_message(mock_request)
            self.assertIn("message", response)
            self.assertEqual(response["message"]["role"], "ROLE_AGENT")
            text = response["message"]["parts"][0]["text"]
            self.assertIn("Added to cart with 10% discount.", text)
            self.assertIn("Recommended Products", text)
            self.assertIn("Slim Jeans", text)


class TestA2AHTTPRoutes(unittest.TestCase):
    """
    End-to-end FastAPI TestClient route tests.
    """

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_route_start_session(self):
        with patch("agents.a2a.service.a2a_service.create_session", new_callable=AsyncMock) as mock_cs:
            mock_cs.return_value = "a2a_test_http_token"
            res = self.client.post("/a2a/start_session")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["chat_token"], "a2a_test_http_token")
            self.assertIn("Session started", data["message"])

    def test_route_agent_card(self):
        res = self.client.get("/.well-known/agent-card.json")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["name"], "Dukaan AI Sales Agent")
        self.assertEqual(data["version"], "1.0.0")

    def test_route_catalog(self):
        with patch("agents.a2a.service.a2a_service.get_catalog_products", new_callable=AsyncMock) as mock_cat:
            mock_p = MagicMock()
            mock_p.id = 5
            mock_p.name = "Oxford Cotton Shirt"
            mock_p.description = "Formal shirt"
            mock_p.price = 999.0
            mock_p.stock = 15
            mock_p.type = "SHIRT"
            mock_cat.return_value = [mock_p]

            res = self.client.get("/a2a/catalog")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["store"], "Dukaan")
            self.assertEqual(len(data["items"]), 1)
            self.assertEqual(data["items"][0]["name"], "Oxford Cotton Shirt")

    def test_route_interact(self):
        with patch("agents.a2a.service.a2a_service.execute_agent_intent", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {
                "status": "success",
                "reply_text": "Cart updated.",
                "suggested_products": [],
            }

            payload = {
                "chat_token": "a2a_token_abc",
                "intent": "Add 2 shirts to cart",
            }
            res = self.client.post("/a2a/interact", json=payload)
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["status"], "success")
            self.assertEqual(data["message"], "Cart updated.")

    def test_route_interact_message_send_jsonrpc(self):
        with patch("agents.a2a.service.a2a_service.execute_agent_intent", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {
                "status": "success",
                "reply_text": "Order created with Razorpay link: https://rzp.io/l/test",
                "suggested_products": [],
            }

            payload = {
                "message": {
                    "role": "user",
                    "parts": [{"text": "Checkout and give me payment link"}]
                },
                "metadata": {
                    "context_id": "a2a_session_buyer_01"
                }
            }
            res = self.client.post("/a2a/interact/message:send", json=payload)
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["message"]["role"], "ROLE_AGENT")
            self.assertIn("Order created with Razorpay link", data["message"]["parts"][0]["text"])


if __name__ == "__main__":
    unittest.main()
