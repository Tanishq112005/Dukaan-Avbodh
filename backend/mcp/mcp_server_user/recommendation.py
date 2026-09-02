from mcp_server_user.server import mcp
from services.upsell_service import upsell_service
from services.behavior_scorer import behavior_scorer
from services.audit_logger import audit_logger
from repositories.cart_repository import cart_repository
from repositories.user_event_repository import UserEventRepository

event_repo = UserEventRepository()


@mcp.tool()
async def recommend_products(user_id: int, thread_id: str = "") -> dict:
    """
    Recommends 3-4 best-matching products using browsing events (empty cart) or complementary
    categories (cart has items), ranked by hybrid score:
    0.5 * event relevance (views, cart adds, suggestion accepted/skipped, purchases) + 0.5 * importance_score.

    LLM Instructions:
    - DO call this tool when the user asks for suggestions or the frontend requests proactive recommendations.
    - DO present 'suggested_products' conversationally.
    - DO pitch 'combo_offer' as a Curated Kit using total_combo_price (already campaign-adjusted).
    - DO NOT expose affinity scores, importance_score, or raw event logs to the user.
    - DO NOT invent extra products or prices.
    """
    cart_items = await cart_repository.get_cart_items(user_id)
    try:
        result = await upsell_service.generate_upsell_offer(user_id, cart_items)
    except Exception as e:
        print(f"ERROR in recommend_products: {str(e)}")
        return {"success": False, "error": f"Failed to generate upsell offer: {str(e)}"}

    if not result.get("success") or not result.get("suggested_products"):
        return {"success": False, "message": "No suitable recommendations found based on current cart and behavior."}

    suggested = result["suggested_products"][:4]
    combo_offer = result.get("combo_offer") or {}

    scores = await behavior_scorer.get_category_affinity(user_id)
    top_category = suggested[0].get("type") if suggested else None
    if hasattr(top_category, "value"):
        top_category = top_category.value
    category_score = scores.get(top_category, 0.0) if top_category else 0.0
    purchase_probability = behavior_scorer.estimate_purchase_probability(category_score)

    recent_events = await event_repo.get_events_for_user(user_id)
    recent_sorted = sorted(recent_events, key=lambda e: e.timestamp, reverse=True)[:5]

    await audit_logger.log_action(
        action="recommend_products",
        reason=(
            f"cart_empty={not cart_items}, top_category={top_category}, "
            f"campaigns={combo_offer.get('applied_campaigns', [])}"
        ),
        result=f"suggested={len(suggested)} kit_price={combo_offer.get('total_combo_price')}",
        user_id=user_id,
        thread_id=str(thread_id) if thread_id else None,
        metadata={
            "suggested_ids": [p.get("id") for p in suggested],
            "combo_offer": combo_offer,
            "applied_campaigns": combo_offer.get("applied_campaigns", []),
        },
    )

    return {
        "success": True,
        "suggested_products": suggested,
        "combo_offer": combo_offer,
        "why": {
            "top_category": top_category,
            "affinity_score": round(category_score, 2),
            "estimated_purchase_probability_percent": purchase_probability,
            "recent_activity": [
                {
                    "event_type": e.event_type.value,
                    "category": e.category,
                    "timestamp": e.timestamp.isoformat(),
                }
                for e in recent_sorted
            ],
        },
    }
