# mcp_server/search.py
from typing import Optional
from mcp_server.server import mcp
from config.embeddingModel import embeddingModel
from config.vectorDatabase import vectorDB
from services.behavior_scorer import behavior_scorer
from repositories.product_repository import ProductRepository
from repositories.cart_repository import cart_repository
from repositories.user_event_repository import UserEventRepository
from models.product import ProductType
from models.user_event import EventType

product_repo = ProductRepository()
event_repo = UserEventRepository()


def _detect_category(query: str) -> Optional[str]:
    """Query text mein se koi valid ProductType keyword dhoondta hai (best-effort)."""
    q = query.lower()
    for t in ProductType:
        if t.value in q:
            return t.value
    return None


@mcp.tool()
async def search_products(user_id: int, query: str, category: Optional[str] = None) -> dict:
    """
    User ki specific search query (jaise 'blue jeans', 'party wear shirt') ke liye
    3-4 matching products dhoondta hai.

    Agar query ek specific category ki taraf point karti hai (jaise 'jeans'), toh
    yeh tool user ke SIRF usi category ke purane events (viewed/purchased/accepted)
    check karta hai — poori affinity list nahi — taaki us category mein unka
    brand/style preference pata chale, aur usi context ke saath vector search
    karke best matches diye jaate hain.

    category param optional hai — agent explicitly bhej sakta hai (jaise 'jeans',
    get_products_by_type se pehle se pata hoga), warna query text se best-effort
    detect ho jaata hai.
    """
    detected_category = category or _detect_category(query)

    # --- Sirf isi category ka past behavior, poori profile nahi ---
    style_context = ""
    category_score = 0.0
    if detected_category:
        all_events = await event_repo.get_events_for_user(user_id)
        relevant_events = [
            e for e in all_events
            if e.category == detected_category
            and e.event_type in (EventType.VIEWED, EventType.PURCHASED, EventType.SUGGESTION_ACCEPTED)
            and e.product_id is not None
        ]
        relevant_events = sorted(relevant_events, key=lambda e: e.timestamp, reverse=True)[:5]

        past_products = []
        for e in relevant_events:
            p = await product_repo.get_by_id(e.product_id)
            if p:
                past_products.append(p.name)

        if past_products:
            style_context = f"User pehle in {detected_category} ko pasand kar chuka hai: {', '.join(past_products)}."

        scores = await behavior_scorer.get_category_affinity(user_id)
        category_score = scores.get(detected_category, 0.0)

    cart_items = await cart_repository.get_cart_items(user_id)
    cart_desc = ", ".join(i["name"] for i in cart_items) if cart_items else "empty"

    enhanced_query = f"{query}. {style_context} Current cart: {cart_desc}".strip()

    embedder = embeddingModel.getModel()
    query_vector = embedder.embed_query(enhanced_query)

    index = vectorDB.get_index("dukaan-products")
    filter_dict = {"category": detected_category} if detected_category else {}
    try:
        search_results = index.query(vector=query_vector, top_k=4, include_metadata=True, filter=filter_dict)
    except Exception as e:
        return {"success": False, "error": f"Vector search failed: {e}"}

    found_items = []
    if search_results and hasattr(search_results, "matches"):
        for match in search_results.matches:
            p = await product_repo.get_by_id(int(match.id))
            if p:
                found_items.append(p.model_dump())

    if not found_items:
        return {"success": False, "message": "Koi matching product nahi mila."}

    return {
        "success": True,
        "products": found_items,
        "why": {
            "detected_category": detected_category,
            "category_affinity_score": round(category_score, 2),
            "past_style_context": style_context or None,
        },
    }
