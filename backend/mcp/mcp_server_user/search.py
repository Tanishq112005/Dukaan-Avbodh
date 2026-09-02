from typing import Optional
import asyncio
from mcp_server_user.server import mcp
from config.embeddingModel import embeddingModel
from config.vectorDatabase import vectorDB
from services.behavior_scorer import behavior_scorer
from services.recommendation_service import recommendation_service
from services.pricing_service import pricing_service
from repositories.product_repository import ProductRepository
from repositories.cart_repository import cart_repository
from repositories.user_event_repository import UserEventRepository
from models.product import ProductType
from models.user_event import EventType

product_repo = ProductRepository()
event_repo = UserEventRepository()


def _detect_category(query: str) -> Optional[str]:
    """Attempts to detect a valid ProductType keyword from the query text."""
    q = query.lower()
    for t in ProductType:
        if t.value in q:
            return t.value
    return None


@mcp.tool()
async def search_products(user_id: int, query: str, category: str) -> dict:
    """
    Performs a semantic vector search, keeps only strong semantic matches, then boosts
    high importance_score inventory. Items that are semantically weak are dropped even if
    they have a high merchant importance score.

    LLM Instructions:
    - DO pass the user's explicit request in the 'query' parameter.
    - DO infer the product category (e.g., 't-shirt', 'jeans', 'shirt', 'hoodie', 'short') from the user's request and pass it in the 'category' argument. 
    - DO NOT leave 'category' empty or None if a specific type is explicitly or implicitly requested, as this drastically improves search accuracy.
    - DO present the returned 'products' to the user in a natural, conversational way.
    - DO NOT expose the 'why' metadata variables (like 'category_affinity_score' or 'past_style_context') to the user. Use them internally to guide your tone.
    - DO NOT fabricate products; only recommend the exact items returned by this tool.
    """
    def log(msg):
        print(msg)
            
    log(f"--- search_products called: {query} / {category} ---")
    
    if not category or category.lower() in ("none", "null", "general", "any", ""):
        category = None
        
    detected_category = category or _detect_category(query)
    log(f"detected_category: {detected_category}")

    try:
        async def do_full_search():
            log("Starting do_full_search")
            style_context = ""
            category_score = 0.0
            
            if detected_category:
                log("Fetching events")
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
                    style_context = f"User previously liked these {detected_category}s: {', '.join(past_products)}."
        
                scores = await behavior_scorer.get_category_affinity(user_id)
                category_score = scores.get(detected_category, 0.0)
        
            log("Fetching cart items")
            cart_items = await cart_repository.get_cart_items(user_id)
            cart_desc = ", ".join(i["name"] for i in cart_items) if cart_items else "empty"
        
            cart_genders = [i.get("gender") for i in cart_items if i.get("gender")]
            if cart_genders:
                target_gender = max(set(cart_genders), key=cart_genders.count)
            else:
                target_gender = await behavior_scorer.get_current_gender_context(user_id)
        
            enhanced_query = f"{query}. {style_context} Current cart: {cart_desc}".strip()
            
            log(f"Getting embedder. Query: {enhanced_query}")
            embedder = embeddingModel.getModel()
            
            log("Calling embed_query (in thread to avoid blocking event loop)")
            query_vector = await asyncio.to_thread(embedder.embed_query, enhanced_query)
            log("Embedding done")
            
            index = vectorDB.get_index("dukaan-products")
            filter_dict = {}
            if detected_category:
                filter_dict["category"] = detected_category
            if target_gender and target_gender != "unisex":
                filter_dict["gender"] = {"$in": [target_gender, "unisex"]}
                
            log("Calling Pinecone index.query")
            res = await asyncio.to_thread(index.query, vector=query_vector, top_k=20, include_metadata=True, filter=filter_dict)
            log("Pinecone done")
            
            return res, style_context, category_score

        log("Waiting for do_full_search with 90s timeout")
        search_results, style_context, category_score = await asyncio.wait_for(do_full_search(), timeout=90.0)
        log("do_full_search finished successfully")
        
    except asyncio.TimeoutError:
        log("TIMEOUT ERROR")
        return {"success": False, "error": "Search timed out after 90 seconds. Please tell the user you are having trouble searching right now."}
    except Exception as e:
        log(f"EXCEPTION: {e}")
        return {"success": False, "error": f"Vector search failed. Tip for agent: The error might be due to a missing category or database timeout."}

    found_hits = []
    if search_results and hasattr(search_results, "matches"):
        for match in search_results.matches:
            p = await product_repo.get_by_id(int(match.id))
            if p:
                found_hits.append((p, float(getattr(match, "score", 0.0) or 0.0)))

    ranked = recommendation_service.rerank_search_hits(found_hits, limit=4)
    if not ranked:
        return {"success": False, "message": "No matching products found."}

    priced = await pricing_service.price_products([p for p, _, _ in ranked])
    priced_by_id = {row["id"]: row for row in priced}

    found_items = []
    for product, combined, semantic in ranked:
        payload = product.model_dump(exclude={"cost_price", "min_profit_margin_percent", "stock", "discount"})
        snapshot = priced_by_id.get(product.id)
        if snapshot:
            payload["new_selling_price"] = snapshot["new_selling_price"]
            payload["applied_campaigns"] = snapshot["applied_campaigns"]
            payload["has_campaign"] = snapshot["has_campaign"]
        payload["semantic_score"] = round(semantic, 4)
        payload["rank_score"] = round(combined, 4)
        found_items.append(payload)

    return {
        "success": True,
        "products": found_items,
        "why": {
            "detected_category": detected_category,
            "category_affinity_score": round(category_score, 2),
            "past_style_context": style_context or None,
        },
    }