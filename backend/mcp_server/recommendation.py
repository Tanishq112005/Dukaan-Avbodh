# mcp_server/recommendation.py
from mcp_server.server import mcp
from services.upsell_service import upsell_service
from services.behavior_scorer import behavior_scorer
from repositories.cart_repository import cart_repository
from repositories.user_event_repository import UserEventRepository

event_repo = UserEventRepository()


@mcp.tool()
async def recommend_products(user_id: int) -> dict:
    """
    User ke current cart + behavior/affinity + recent activity ke hisaab se
    3-4 best matching product suggest karta hai. Behavior data (affinity score,
    recent events, purchase probability) is tool ke andar hi fetch ho jaata hai —
    agent ko alag se get_user_affinity/get_recent_events/calculate_purchase_probability
    call karne ki zaroorat nahi.

    Yeh tab call karo jab:
    - user ne is session mein kaafi products browse/view kar liye hon, YA
    - user khud suggestions maange ("kuch aur dikhao", "iske saath kya achha lagega").
    """
    cart_items = await cart_repository.get_cart_items(user_id)
    result = await upsell_service.generate_upsell_offer(user_id, cart_items)

    if not result.get("success") or not result.get("suggested_products"):
        return {"success": False, "message": "Abhi cart/behavior ke hisaab se koi achha match nahi mila."}

    suggested = result["suggested_products"][:4]

    # --- Behavior context, ab yahin integrate ---
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
