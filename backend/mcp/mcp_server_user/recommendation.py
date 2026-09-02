# mcp_server/recommendation.py
from mcp_server_user.server import mcp
from services.upsell_service import upsell_service
from services.behavior_scorer import behavior_scorer
from repositories.cart_repository import cart_repository
from repositories.user_event_repository import UserEventRepository

event_repo = UserEventRepository()


@mcp.tool()
async def recommend_products(user_id: int) -> dict:
    """
    Recommends 3-4 best-matching products based on the user's current cart, behavior affinity, and recent browsing activity.
    This tool automatically fetches all necessary behavioral context internally.

    LLM Instructions:
    - DO call this tool when the user explicitly asks for suggestions (e.g., "what else should I buy?", "what matches with this?").
    - DO call this tool proactively to upsell if the user has items in their cart and is actively engaged.
    - DO present the 'suggested_products' to the user in a friendly, conversational manner.
    - DO use the 'why' metadata internally to personalize your pitch (e.g., if you see they recently viewed a category, naturally mention it).
    - DO NOT expose the raw 'why' metadata variables (such as 'affinity_score', 'estimated_purchase_probability_percent', or raw 'recent_activity' logs) to the user. Keep the data hidden.
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

    # --- Behavior context, integrated internally ---
    scores = await behavior_scorer.get_category_affinity(user_id)

    top_category = suggested[0].get("type") if suggested else None
    category_score = scores.get(top_category, 0.0) if top_category else 0.0
    purchase_probability = behavior_scorer.estimate_purchase_probability(category_score)

    recent_events = await event_repo.get_events_for_user(user_id)
    recent_sorted = sorted(recent_events, key=lambda e: e.timestamp, reverse=True)[:5]

    return {
        "success": True,
        "suggested_products": suggested,
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