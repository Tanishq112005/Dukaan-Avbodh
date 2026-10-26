import logging
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from langchain_core.messages import HumanMessage

from Merchant.database import merchantRepository
from Merchant.schemas import (
    CreateCampaignRequest,
    UpdateCampaignRequest,
    PricingBoundsUpdateRequest,
)
from Merchant.utils import assert_merchant_access
from services.audit_logger import audit_logger

logger = logging.getLogger(__name__)


class MerchantController:
    """
    Business logic and operational controller for the Merchant domain:
    - Executive business intelligence and analytics
    - Inventory reordering and stock alerts
    - Customer orders and fulfillment status
    - Promotional campaigns and pricing policy bounds
    - Conversational merchant assistant
    """

    def __init__(self, repository=merchantRepository):
        self.repo = repository

    # --------------------------------------------------------------------------
    # 1. Dashboard Analytics
    # --------------------------------------------------------------------------
    async def get_dashboard_analytics(self, time_range: str = "all") -> Dict[str, Any]:
        """Fetches aggregated real-time metrics, revenue trends, and inventory alerts."""
        try:
            return await self.repo.get_dashboard_analytics(time_range=time_range)
        except Exception as e:
            logger.exception("[MERCHANT CONTROLLER] Failed to compute analytics: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve merchant dashboard analytics: {str(e)}",
            )

    # --------------------------------------------------------------------------
    # 2. Orders Management
    # --------------------------------------------------------------------------
    async def get_all_orders(
        self,
        limit: int = 100,
        skip: int = 0,
        order_status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetches customer orders with product and user details."""
        try:
            return await self.repo.get_all_orders(limit=limit, skip=skip, status=order_status)
        except Exception as e:
            logger.exception("[MERCHANT CONTROLLER] Failed to fetch orders: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve merchant orders: {str(e)}",
            )

    async def get_order_detail(self, order_id: int) -> Dict[str, Any]:
        """Fetches single order details by ID."""
        order = await self.repo.get_order_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with ID {order_id} not found.",
            )
        return order

    async def update_order_status(
        self,
        order_id: int,
        new_status: str,
        current_user: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Updates payment/fulfillment status of an order and records an audit log."""
        updated = await self.repo.update_order_payment_status(order_id, new_status)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} could not be found to update.",
            )

        merchant_id = current_user.get("user_id") if current_user else 1
        await audit_logger.log_event(
            event_type="order_status_update",
            user_id=merchant_id,
            details={
                "order_id": order_id,
                "new_status": new_status,
                "updated_by_role": "merchant",
            },
        )

        return {
            "success": True,
            "order_id": order_id,
            "status": updated.payment_status,
            "message": f"Order #{order_id} status updated to '{new_status}'.",
        }

    # --------------------------------------------------------------------------
    # 3. Inventory & Low Stock Alerts
    # --------------------------------------------------------------------------
    async def get_inventory_alerts(self, threshold: int = 10) -> List[Dict[str, Any]]:
        """Returns catalog items that are out of stock or low in inventory."""
        try:
            return await self.repo.get_inventory_alerts(threshold=threshold)
        except Exception as e:
            logger.exception("[MERCHANT CONTROLLER] Inventory alert fetch failed: %s", e)
            return []

    # --------------------------------------------------------------------------
    # 4. Audit Logs & Chat Transcripts
    # --------------------------------------------------------------------------
    async def get_audit_logs(self, limit: int = 200) -> Dict[str, Any]:
        """Fetches system and monetary audit trail from MongoDB."""
        logs = await self.repo.get_audit_logs(limit=limit)
        return {"logs": logs}

    async def get_chat_transcripts(self, limit: int = 100) -> Dict[str, Any]:
        """Fetches AI customer conversation threads and negotiation logs."""
        threads = await self.repo.get_chat_threads(limit=limit)
        return {"threads": threads}

    # --------------------------------------------------------------------------
    # 5. Campaign Management
    # --------------------------------------------------------------------------
    async def create_campaign(
        self,
        payload: CreateCampaignRequest,
        current_user: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Creates a new marketing campaign and adjusts catalog importance scores."""
        try:
            campaign = await self.repo.create_campaign(
                agenda=payload.agenda,
                discount_percentage=payload.discount_percentage,
                priority=payload.priority,
                type=payload.type,
                product_ids=payload.product_ids,
            )

            merchant_id = current_user.get("user_id") if current_user else 1
            await audit_logger.log_event(
                event_type="campaign_created",
                user_id=merchant_id,
                details={
                    "campaign_id": campaign.id,
                    "agenda": campaign.agenda,
                    "discount_percentage": campaign.discount_percentage,
                    "linked_products": len(payload.product_ids),
                },
            )

            return {
                "success": True,
                "message": f"Campaign '{campaign.agenda}' created successfully.",
                "campaign": campaign.model_dump() if hasattr(campaign, "model_dump") else campaign,
            }
        except Exception as e:
            logger.exception("[MERCHANT CONTROLLER] Campaign creation failed: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create campaign: {str(e)}",
            )

    async def get_campaigns(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Lists active promotional campaigns with linked products and stock counts."""
        return await self.repo.get_all_campaigns(skip=skip, limit=limit)

    async def get_campaign_detail(self, campaign_id: int) -> Dict[str, Any]:
        """Retrieves details of a specific campaign."""
        camp = await self.repo.get_campaign_by_id(campaign_id)
        if not camp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign with ID {campaign_id} not found.",
            )
        return camp

    async def delete_campaign(
        self,
        campaign_id: int,
        current_user: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Deletes a promotional campaign and resets product weights."""
        success = await self.repo.delete_campaign(campaign_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign with ID {campaign_id} not found to delete.",
            )

        merchant_id = current_user.get("user_id") if current_user else 1
        await audit_logger.log_event(
            event_type="campaign_deleted",
            user_id=merchant_id,
            details={"campaign_id": campaign_id},
        )

        return {"success": True, "message": f"Campaign #{campaign_id} deleted successfully."}

    # --------------------------------------------------------------------------
    # 6. Dynamic Pricing Bounds Policy
    # --------------------------------------------------------------------------
    async def get_pricing_bounds(self) -> Dict[str, Any]:
        """Retrieves currently enforced dynamic pricing negotiation limits."""
        policy = await self.repo.get_or_create_discount_policy()
        return {
            "max_discount_percentage": policy.max_discount_percentage,
            "min_margin_percentage": policy.min_margin_percentage,
            "auto_accept_threshold": policy.auto_accept_threshold,
            "updated_at": policy.updated_at.isoformat() if policy.updated_at else None,
        }

    async def update_pricing_bounds(
        self,
        payload: PricingBoundsUpdateRequest,
        current_user: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Updates merchant bounds for AI buyer-agent negotiations."""
        updated = await self.repo.update_discount_policy(
            merchant_id=current_user.get("user_id", 1) if current_user else 1,
            max_discount_percentage=payload.max_discount_percentage,
            min_margin_percentage=payload.min_margin_percentage,
            auto_accept_threshold=payload.auto_accept_threshold,
        )

        merchant_id = current_user.get("user_id") if current_user else 1
        await audit_logger.log_event(
            event_type="pricing_bounds_updated",
            user_id=merchant_id,
            details={
                "max_discount_percentage": updated.max_discount_percentage,
                "min_margin_percentage": updated.min_margin_percentage,
                "auto_accept_threshold": updated.auto_accept_threshold,
            },
        )

        return {
            "success": True,
            "message": "Pricing negotiation bounds updated successfully.",
            "policy": {
                "max_discount_percentage": updated.max_discount_percentage,
                "min_margin_percentage": updated.min_margin_percentage,
                "auto_accept_threshold": updated.auto_accept_threshold,
            },
        }

    # --------------------------------------------------------------------------
    # 7. Merchant AI Assistant
    # --------------------------------------------------------------------------
    async def chat(
        self,
        text: str,
        thread_id: Optional[str] = None,
        current_user: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes query through the specialized LangGraph Merchant Agent.
        """
        try:
            from agents.merchant import agent_service as merchant_agent_service

            agent = merchant_agent_service.get_merchant_agent()
            user_id = current_user.get("user_id") if current_user else 1
            thread = thread_id or f"merchant_{user_id}"
            config = {"configurable": {"thread_id": thread}}

            initial_state = {
                "messages": [HumanMessage(content=text)],
                "user_id": user_id,
                "thread_id": thread,
            }

            result = await agent.ainvoke(initial_state, config=config)
            ai_reply = result.get("final_response", "Request processed.")

            return {
                "type": "merchant_chat_reply",
                "message": ai_reply,
            }
        except Exception as e:
            logger.exception("[MERCHANT CONTROLLER] AI agent interaction failed: %s", e)
            return {
                "type": "merchant_chat_reply",
                "message": "I am experiencing difficulty accessing store data right now. Please ensure background services are running.",
            }


merchantController = MerchantController()
