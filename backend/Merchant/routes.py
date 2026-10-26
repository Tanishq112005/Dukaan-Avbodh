import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from middleware.merchant_middleware import require_role
from User.models import UserRole
from Merchant.controller import merchantController
from Merchant.schemas import (
    CreateCampaignRequest,
    UpdateOrderStatusRequest,
    PricingBoundsUpdateRequest,
    MerchantChatRequest,
    MerchantChatResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/merchant", tags=["Merchant"])


# ==============================================================================
# 1. Storefront Analytics & Executive Metrics
# ==============================================================================

@router.get("/analytics")
async def get_analytics(
    time_range: str = Query("all", description="Time window for metrics: 'today', '7d', '30d', or 'all'"),
    current_user: dict = Depends(require_role(UserRole.MERCHANT)),
):
    """
    Fetches real-time multi-channel business intelligence: gross revenue, net profit,
    storewide profit margins, top-selling products, category revenue, daily trendlines,
    inventory alerts, and AI customer negotiation funnel metrics.
    """
    return await merchantController.get_dashboard_analytics(time_range=time_range)


# ==============================================================================
# 2. Orders Management
# ==============================================================================

@router.get("/orders")
async def get_all_orders(
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    order_status: Optional[str] = Query(None, description="Filter by status (e.g. 'paid', 'placed', 'shipped')"),
    current_user: dict = Depends(require_role(UserRole.MERCHANT)),
):
    """Fetches customer orders grouped by gateway order ID with product and shipping details."""
    orders = await merchantController.get_all_orders(limit=limit, skip=skip, order_status=order_status)
    return {"orders": orders}


@router.get("/orders/{order_id}")
async def get_order_by_id(
    order_id: int,
    current_user: dict = Depends(require_role(UserRole.MERCHANT)),
):
    """Fetches specific order details including line item pricing and payment status."""
    return await merchantController.get_order_detail(order_id)


@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    payload: UpdateOrderStatusRequest,
    current_user: dict = Depends(require_role(UserRole.MERCHANT)),
):
    """Updates order fulfillment/payment status (e.g. 'shipped', 'delivered') and logs an audit trail."""
    return await merchantController.update_order_status(
        order_id=order_id,
        new_status=payload.status,
        current_user=current_user,
    )


# ==============================================================================
# 3. Inventory Health & Reorder Alerts
# ==============================================================================

@router.get("/inventory-alerts")
async def get_inventory_alerts(
    threshold: int = Query(10, ge=0, description="Stock limit below which products are flagged"),
    current_user: dict = Depends(require_role(UserRole.MERCHANT)),
):
    """Lists catalog products that are out of stock or running low on inventory."""
    alerts = await merchantController.get_inventory_alerts(threshold=threshold)
    return {"alerts": alerts}


# ==============================================================================
# 4. Auditing & Customer Chat Transcripts (MongoDB)
# ==============================================================================

@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = Query(200, ge=1, le=500),
    current_user: dict = Depends(require_role(UserRole.MERCHANT)),
):
    """Fetches system and monetary audit trail from MongoDB."""
    return await merchantController.get_audit_logs(limit=limit)


@router.get("/chat-threads")
async def get_all_chat_threads(
    limit: int = Query(100, ge=1, le=200),
    current_user: dict = Depends(require_role(UserRole.MERCHANT)),
):
    """Fetches user conversational shopping sessions and AI negotiation history."""
    return await merchantController.get_chat_transcripts(limit=limit)


# ==============================================================================
# 5. Marketing Campaigns Management
# ==============================================================================

@router.get("/campaigns")
async def list_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user: dict = Depends(require_role(UserRole.MERCHANT)),
):
    """Lists all active promotional campaigns and linked product details."""
    campaigns = await merchantController.get_campaigns(skip=skip, limit=limit)
    return {"campaigns": campaigns}


@router.post("/campaigns", status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CreateCampaignRequest,
    current_user: dict = Depends(require_role(UserRole.MERCHANT)),
):
    """Creates a new marketing campaign and adjusts catalog product importance scores."""
    return await merchantController.create_campaign(payload=payload, current_user=current_user)


@router.get("/campaigns/{campaign_id}")
async def get_campaign(
    campaign_id: int,
    current_user: dict = Depends(require_role(UserRole.MERCHANT)),
):
    """Fetches details of a specific promotional campaign."""
    return await merchantController.get_campaign_detail(campaign_id)


@router.delete("/campaigns/{campaign_id}")
async def delete_campaign(
    campaign_id: int,
    current_user: dict = Depends(require_role(UserRole.MERCHANT)),
):
    """Deletes a promotional campaign and resets associated product importance scores."""
    return await merchantController.delete_campaign(campaign_id=campaign_id, current_user=current_user)


# ==============================================================================
# 6. Pricing Negotiation Bounds
# ==============================================================================

@router.get("/pricing-bounds")
async def get_pricing_bounds(
    current_user: dict = Depends(require_role(UserRole.MERCHANT)),
):
    """Retrieves storewide dynamic pricing bounds enforced during AI negotiations."""
    return await merchantController.get_pricing_bounds()


@router.put("/pricing-bounds")
async def update_pricing_bounds(
    payload: PricingBoundsUpdateRequest,
    current_user: dict = Depends(require_role(UserRole.MERCHANT)),
):
    """Updates maximum permissible discount and floor profit margins for AI bargaining."""
    return await merchantController.update_pricing_bounds(payload=payload, current_user=current_user)


# ==============================================================================
# 7. Conversational Merchant AI Co-Pilot
# ==============================================================================

@router.post("/chat", response_model=MerchantChatResponse)
async def chat_with_merchant_agent(
    req: MerchantChatRequest,
    current_user: dict = Depends(require_role(UserRole.MERCHANT)),
):
    """Processes analytical and catalog management queries through the Merchant AI Agent."""
    res = await merchantController.chat(
        text=req.text,
        thread_id=req.thread_id,
        current_user=current_user,
    )
    return res
