# mcp_server/behavior.py
from mcp_server.server import mcp
from services.behavior_scorer import behavior_scorer
from repositories.user_event_repository import UserEventRepository

event_repo = UserEventRepository()

@mcp.tool()
async def get_user_affinity(user_id: int) -> dict:
    """User ke events ke hisaab se uski category preferences (affinity score) return karta hai.
    Agent isse padhkar recommend kar sakta hai ki user ko kya pasand aayega."""
    try:
        scores = await behavior_scorer.get_category_affinity(user_id)
        if not scores:
            return {"success": True, "message": "User ka abhi tak koi behavior data nahi hai.", "scores": {}}
        
        # Sabse zyada pasand aane wali categories pehle (Descending order)
        sorted_scores = dict(sorted(scores.items(), key=lambda item: item[1], reverse=True))
        return {"success": True, "scores": sorted_scores}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_recent_events(user_id: int, limit: int = 5) -> list[dict]:
    """User ke hal hi (recent) ke events fetch karta hai, jaise usne kya VIEWED ya PURCHASED kiya."""
    events = await event_repo.get_events_for_user(user_id)
    
    # Latest events pehle
    recent_events = sorted(events, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    return [
        {
            "event_type": e.event_type.value,
            "product_id": e.product_id,
            "category": e.category,
            "timestamp": e.timestamp.isoformat()
        } for e in recent_events
    ]
    
    
@mcp.tool()
async def calculate_purchase_probability(user_id: int, category: str) -> dict:
    """
    Kisi ek specific category (jaise 't-shirt' ya 'jeans') ke liye user ka score
    aur purchase karne ki estimated probability calculate karta hai.
    """
    try:
        # Pura score map nikalenge
        scores = await behavior_scorer.get_category_affinity(user_id)
        
        # Sirf us category ka score nikalenge jo agent ne pucha hai
        category_score = scores.get(category, 0.0)
        
        # Probability logic (tum isko apne hisaab se adjust kar sakte ho)
        # Agar score 0 hai toh low chance, agar 10+ hai toh high chance
        probability = min(95.0, max(5.0, category_score * 10))
        
        return {
            "success": True,
            "category": category,
            "affinity_score": round(category_score, 2),
            "estimated_purchase_probability_percent": round(probability, 2),
            "recommendation": "High probability, definitely upsell!" if probability > 50 else "Low probability, offer high discount to convert."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}    