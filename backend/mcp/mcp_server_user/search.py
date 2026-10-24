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
from repositories.userEvent import UserEventRepository
from models.product import ProductType
from models.user_event import EventType
from langsmith import traceable

product_repo = ProductRepository()
event_repo = UserEventRepository()

def _detect_category(query: str) -> Optional[str]:
    """Attempts to detect a valid ProductType keyword from the query text."""
    q = query.lower()
    for t in ProductType:
        if t.value in q:
            return t.value
    return None

def log(msg):
    print(msg)

# ---------------------------------------------------------
# STEP 1: Build User Context (Events, Cart, Gender)
# ---------------------------------------------------------
async def _empty_dict():
    return {}

async def _empty_list():
    return []

@traceable(run_type="chain", name="build_search_context")
async def _build_search_context(user_id: int, query: str, detected_category: Optional[str]) -> dict:
    log("Building search context...")
    style_context = ""
    category_score = 0.0

    # 1. Fetch user events ONCE to avoid redundant DB queries in downstream tasks
    all_events = await event_repo.get_events_for_user(user_id)
    
    # 2. Run independent DB/service calls concurrently
    cart_task = cart_repository.get_cart_items(user_id)
    affinity_task = behavior_scorer.get_category_affinity(user_id, events=all_events) if detected_category else _empty_dict()
    gender_ctx_task = behavior_scorer.get_current_gender_context(user_id, events=all_events)

    cart_items, scores, fallback_gender = await asyncio.gather(
        cart_task, affinity_task, gender_ctx_task
    )

    # 1. Build style context from relevant past events
    if detected_category:
        relevant_events = [
            e for e in all_events
            if e.category == detected_category
            and e.event_type in (EventType.VIEWED, EventType.PURCHASED, EventType.SUGGESTION_ACCEPTED)
            and e.product_id is not None
        ]
        relevant_events = sorted(relevant_events, key=lambda e: e.timestamp, reverse=True)[:5]

        # Fetch all past products in a single database batch query (Fixes N+1 problem)
        product_ids = [e.product_id for e in relevant_events]
        past_products_results = await product_repo.get_by_ids(product_ids) if product_ids else []
        
        past_products = [p.name for p in past_products_results if p]

        if past_products:
            style_context = f"User previously liked these {detected_category}s: {', '.join(past_products)}."

        category_score = scores.get(detected_category, 0.0)

    # 2. Cart context
    cart_desc = ", ".join(i["name"] for i in cart_items) if cart_items else "empty"

    # 3. Determine target gender
    cart_genders = [i.get("gender") for i in cart_items if i.get("gender")]
    if cart_genders:
        target_gender = max(set(cart_genders), key=cart_genders.count)
    else:
        target_gender = fallback_gender

    enhanced_query = f"{query}. {style_context} Current cart: {cart_desc}".strip()
    
    return {
        "enhanced_query": enhanced_query,
        "style_context": style_context,
        "category_score": category_score,
        "target_gender": target_gender
    }

# ---------------------------------------------------------
# STEP 2: Vector Search (Embeddings + Pinecone)
# ---------------------------------------------------------
@traceable(run_type="retriever", name="execute_vector_search")
async def _execute_vector_search(enhanced_query: str, detected_category: Optional[str], target_gender: Optional[str]):
    log(f"Getting embedder. Query: {enhanced_query}")
    embedder = embeddingModel.getModel()
    
    log("Calling embed_query (in thread to avoid blocking event loop)")
    query_vector_np = await asyncio.to_thread(embedder.encode, enhanced_query)
    query_vector = query_vector_np.tolist()
    index = vectorDB.get_index("dukaan-products")
    filter_dict = {}
    if detected_category:
        filter_dict["category"] = detected_category
    if target_gender and target_gender != "unisex":
        filter_dict["gender"] = {"$in": [target_gender, "unisex"]}
        
    log("Calling Pinecone index.query")
    res = await asyncio.to_thread(index.query, vector=query_vector, top_k=20, include_metadata=True, filter=filter_dict)
    return res

# ---------------------------------------------------------
# STEP 3: Hydrate Data and Rerank
# ---------------------------------------------------------
@traceable(run_type="chain", name="hydrate_and_rerank")
async def _hydrate_and_rerank(search_results):
    found_hits = []
    if search_results and hasattr(search_results, "matches"):
        matches = search_results.matches
        match_ids = [int(match.id) for match in matches]

        # Single batched fetch instead of one get_by_id() call per match (was N sequential DB round-trips for top_k=20).
        products = await product_repo.get_by_ids(match_ids) if match_ids else []
        products_by_id = {p.id: p for p in products}

        for match in matches:
            p = products_by_id.get(int(match.id))
            if p:
                found_hits.append((p, float(getattr(match, "score", 0.0) or 0.0)))

    return recommendation_service.rerank_search_hits(found_hits, limit=4)

# ---------------------------------------------------------
# STEP 4: Apply Pricing and Format Final Response
# ---------------------------------------------------------
@traceable(run_type="chain", name="price_and_format")
async def _price_and_format(ranked_products, detected_category, category_score, style_context):
    priced = await pricing_service.price_products([p for p, _, _ in ranked_products])
    priced_by_id = {row["id"]: row for row in priced}

    found_items = []
    for product, combined, semantic in ranked_products:
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

# ---------------------------------------------------------
# MAIN TOOL: Orchestrator
# ---------------------------------------------------------
@mcp.tool()
@traceable(run_type="tool", name="search_products") 
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
    log(f"--- search_products called: {query} / {category} ---")
    
    if not category or category.lower() in ("none", "null", "general", "any", ""):
        category = None
        
    detected_category = category or _detect_category(query)
    log(f"detected_category: {detected_category}")

    # Helper function to wrap context building + search for the timeout
    async def do_full_search():
        ctx = await _build_search_context(user_id, query, detected_category)
        res = await _execute_vector_search(ctx["enhanced_query"], detected_category, ctx["target_gender"])
        return res, ctx["style_context"], ctx["category_score"]

    try:
        log("Waiting for do_full_search with 90s timeout")
        search_results, style_context, category_score = await asyncio.wait_for(do_full_search(), timeout=90.0)
        log("do_full_search finished successfully")
        
    except asyncio.TimeoutError:
        log("TIMEOUT ERROR")
        return {"success": False, "error": "Search timed out after 90 seconds. Please tell the user you are having trouble searching right now."}
    except Exception as e:
        log(f"EXCEPTION: {e}")
        return {"success": False, "error": f"Vector search failed. Tip for agent: The error might be due to a missing category or database timeout."}

    # Hydrate and Rerank
    ranked = await _hydrate_and_rerank(search_results)
    if not ranked:
        return {"success": False, "message": "No matching products found."}

    # Price and Format
    final_response = await _price_and_format(ranked, detected_category, category_score, style_context)
    return final_response