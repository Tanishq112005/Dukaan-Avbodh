# mcp_server/search.py
from mcp_server.server import mcp
from config.embeddingModel import embeddingModel
from config.vectorDatabase import vectorDB
from services.behavior_scorer import behavior_scorer
from repositories.product_repository import ProductRepository
from repositories.cart_repository import cart_repository

product_repo = ProductRepository()


@mcp.tool()
async def search_products(user_id: int, query: str) -> dict:
    """
    User ki specific search query (jaise 'blue jeans', 'party wear shirt') ke liye
    unke current cart aur style preferences (behavior score) ke context ke saath
    3-4 matching products dhoondta hai. Use jab user koi specific item type maange."""
    scores = await behavior_scorer.get_category_affinity(user_id)
    preferred_categories = []
    if scores:
        sorted_categories = sorted(scores, key=scores.get, reverse=True)
        preferred_categories = sorted_categories[:2]

    cart_items = await cart_repository.get_cart_items(user_id)
    cart_desc = ", ".join(i["name"] for i in cart_items) if cart_items else "empty"

    preferences_text = (
        f"User style context: prefers {', '.join(preferred_categories)}" if preferred_categories else ""
    )
    enhanced_query = f"{query}. {preferences_text}. Current cart: {cart_desc}".strip()

    embedder = embeddingModel.getModel()
    query_vector = embedder.embed_query(enhanced_query)

    index = vectorDB.get_index("dukaan-products")
    try:
        search_results = index.query(vector=query_vector, top_k=4, include_metadata=True)
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
            "preferred_categories_used": preferred_categories,
        },
    }
