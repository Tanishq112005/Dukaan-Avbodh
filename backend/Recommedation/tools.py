import sys
import os
from typing import Optional, Dict, Any, List

# Ensure backend/mcp directory is discoverable for importing FastMCP user server
mcp_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp"))

if mcp_path not in sys.path:
    sys.path.insert(0, mcp_path)

from mcp_server_user.server import mcp
from Product.models import Product, ProductType
from Recommedation.controller import recommedationController
from UserEvents.models import EventType
from UserEvents.tracker import record_bulk_user_events
from langchain_core.tools import StructuredTool


LOGIN_NUDGE_PROMPT = (
    "For personalized recommendations tailored specifically to your style and size, "
    "please log in or sign up to Dukaan!"
)


def _sanitize_product(product: Product) -> Dict[str, Any]:
    """
    Sanitizes product data for LLM consumption, stripping sensitive merchant
    wholesale economics (cost_price, min_profit_margin_percent) as well as
    confidential merchant discount limits, discount percentages, and minimum selling prices.
    Only public standard listing price ('price') is passed to LLM recommendation tools.
    """
    data = product.model_dump(
        exclude={
            "cost_price",
            "min_profit_margin_percent",
            "discount",
            "discount_percentage",
            "discount_percent",
            "min_selling_price",
            "minimum_selling_price",
            "min_price",
        }
    )

    if hasattr(product.type, "value"):
        data["type"] = product.type.value

    # Defensive guard to guarantee no discount percentage or minimum selling price leaks
    for forbidden in (
        "cost_price",
        "min_profit_margin_percent",
        "discount",
        "discount_percentage",
        "discount_percent",
        "min_selling_price",
        "minimum_selling_price",
        "min_price",
    ):
        data.pop(forbidden, None)

    return data


# ==============================================================================
# FastMCP Catalog & Category Resources
# ==============================================================================

@mcp.resource("catalog://product-categories")
async def get_product_categories_resource() -> Dict[str, Any]:
    """
    Returns all valid clothing categories and definitions available in Dukaan.
    
    LLM Instructions:
    - ALWAYS consult this resource to ensure you pass an exact, valid category name.
    - Valid types: 't-shirt', 'jeans', 'shirt', 'hoodie', 'short'.
    """
    return {
        "categories": [
            {
                "type": ProductType.T_SHIRT.value,
                "description": "Casual t-shirts, graphic tees, polo t-shirts, oversized t-shirts",
            },
            {
                "type": ProductType.JEANS.value,
                "description": "Denim jeans: baggy, loose fit, slim fit, tapered, flared, high-rise",
            },
            {
                "type": ProductType.SHIRT.value,
                "description": "Casual shirts, formal shirts, spread collar, striped, checkered",
            },
            {
                "type": ProductType.HOODIE.value,
                "description": "Hoodies, sweatshirts, pullovers, winter wear",
            },
            {
                "type": ProductType.SHORT.value,
                "description": "Casual shorts, denim shorts, lounge shorts",
            },
        ],
        "allowed_values": [t.value for t in ProductType],
    }


@mcp.resource("catalog://genders")
async def get_genders_resource() -> Dict[str, Any]:
    """
    Returns valid gender filter options recognized by Dukaan recommendation algorithms.
    """
    return {
        "allowed_genders": ["men", "women", "unisex"],
        "description": "Use 'men' for men's apparel, 'women' for women's apparel, or 'unisex' for neutral/all.",
    }


# ==============================================================================
# FastMCP Recommendation & Discovery Tools
# ==============================================================================

@mcp.tool()
async def search_and_recommend_by_type(
    product_type: str,
    user_id: Optional[int] = None,
    user_query: str = "",
    gender: Optional[str] = None,
    limit: int = 5,
) -> Dict[str, Any]:
    """
    Searches and recommends in-stock products filtered strictly by category (product_type)
    and optional gender, ranked by semantic query similarity blended with user probability.
    
    Parameters:
    - product_type (str, Required): Target category. Must be one of: 't-shirt', 'jeans', 'shirt', 'hoodie', 'short'.
    - user_id (int, Optional): Customer ID for personalized ranking.
    - user_query (str, Optional): Keywords or style preferences (e.g. 'black baggy', 'cotton floral', 'loose fit').
    - gender (str, Optional): Gender filter: 'men', 'women', or 'unisex'.
    - limit (int, Optional, default=5): Number of in-stock items to return.
    
    LLM Usage & Instructions:
    1. Call this tool when the customer mentions a specific clothing category and describes what they want.
    2. All returned items are strictly confirmed in stock (stock > 0).
    3. Products contain only standard listing price ('price'). Confidential discount percentages and minimum selling prices are strictly excluded.
    4. NEVER invent or present an upfront discount. If the user bargains, invoke 'negotiate_product_discount'.
    3. If user_id is NOT provided (or user is a guest/unauthenticated):
       Present these recommendations and ALWAYS conclude your response with:
       "For personalized recommendations tailored specifically to your style and size, please log in or sign up to Dukaan!"
    4. NEVER fabricate products, prices, or product IDs. Use only the products returned by this tool.
    """
    is_guest = user_id is None or user_id <= 0
    effective_user_id = user_id if not is_guest else 1

    try:
        raw_results = await recommedationController.recommedTheUserProductByTypeAndQuery(
            user_id=effective_user_id,
            product_type=product_type,
            gender=gender,
            user_query=user_query,
            limit=limit,
        )

        sanitized_items = []

        for item in raw_results:
            p = item.get("product")
            if p:
                sanitized_items.append({
                    "product_id": p.id,
                    "product": _sanitize_product(p),
                    "rank_score": item.get("rank_score", item.get("score", 0.0)),
                    "cosine_similarity": item.get("cosine_similarity", 0.0),
                    "source": item.get("source", "recommendation_engine"),
                })

        # Track user events: VIEWED for recommended items only if user_id is provided (> 0)
        if not is_guest and user_id and sanitized_items:
            product_ids = [item["product_id"] for item in sanitized_items if item.get("product_id")]
            categories = {
                item["product_id"]: (item["product"].get("type") or product_type or "general")
                for item in sanitized_items
                if item.get("product_id")
            }
            await record_bulk_user_events(
                user_id=user_id,
                product_ids=product_ids,
                event_type=EventType.VIEWED,
                categories=categories,
            )

        return {
            "success": True,
            "count": len(sanitized_items),
            "category": product_type,
            "products": sanitized_items,
            "requires_login_for_personalization": is_guest,
            "login_prompt": LOGIN_NUDGE_PROMPT if is_guest else None,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to fetch recommendations by type: {str(e)}",
        }


@mcp.tool()
async def recommend_by_query(
    user_query: str,
    user_id: Optional[int] = None,
    gender: Optional[str] = None,
    limit: int = 5,
) -> Dict[str, Any]:
    """
    Searches across all product categories using natural language semantic query matching,
    blended with personalized user preferences and stock verification.
    
    Parameters:
    - user_query (str, Required): Natural language search terms (e.g. 'outfit for college', 'something casual in black').
    - user_id (int, Optional): Customer ID for personalized probability scoring.
    - gender (str, Optional): Gender filter ('men', 'women', 'unisex').
    - limit (int, Optional, default=5): Number of in-stock items to return.
    
    LLM Usage & Instructions:
    1. Call this tool when the customer makes an open-ended search across categories.
    2. Products contain only standard listing price ('price'). Confidential discount percentages and minimum selling prices are strictly excluded.
    3. If user_id is NOT provided (or user is a guest/unauthenticated):
       Present these recommendations and ALWAYS conclude your response with:
       "For personalized recommendations tailored specifically to your style and size, please log in or sign up to Dukaan!"
    4. DO NOT invent extra products, upfront discounts, or prices.
    """
    is_guest = user_id is None or user_id <= 0
    effective_user_id = user_id if not is_guest else 1

    try:
        raw_results = await recommedationController.recommedTheUserProductThroughQuery(
            user_id=effective_user_id,
            gender=gender,
            user_query=user_query,
            limit=limit,
        )

        sanitized_items = []

        for item in raw_results:
            p = item.get("product")
            if p:
                sanitized_items.append({
                    "product_id": p.id,
                    "product": _sanitize_product(p),
                    "rank_score": item.get("rank_score", item.get("score", 0.0)),
                    "cosine_similarity": item.get("cosine_similarity", 0.0),
                    "source": item.get("source", "recommendation_engine"),
                })

        # Track user events: VIEWED for recommended items only if user_id is provided (> 0)
        if not is_guest and user_id and sanitized_items:
            product_ids = [item["product_id"] for item in sanitized_items if item.get("product_id")]
            categories = {
                item["product_id"]: (item["product"].get("type") or "general")
                for item in sanitized_items
                if item.get("product_id")
            }
            await record_bulk_user_events(
                user_id=user_id,
                product_ids=product_ids,
                event_type=EventType.VIEWED,
                categories=categories,
            )

        return {
            "success": True,
            "count": len(sanitized_items),
            "query": user_query,
            "products": sanitized_items,
            "requires_login_for_personalization": is_guest,
            "login_prompt": LOGIN_NUDGE_PROMPT if is_guest else None,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to fetch recommendations by query: {str(e)}",
        }


@mcp.tool()
async def get_personalized_recommendations(
    user_id: Optional[int] = None,
    gender: Optional[str] = None,
    product_type: Optional[str] = None,
    limit: int = 5,
) -> Dict[str, Any]:
    """
    Returns personalized top in-stock product recommendations for a customer based
    on their browsing, carting, and purchasing history.
    
    Parameters:
    - user_id (int, Optional): Customer ID.
    - gender (str, Optional): Gender filter ('men', 'women', 'unisex').
    - product_type (str, Optional): Optional category filter ('t-shirt', 'jeans', 'shirt', 'hoodie', 'short').
    - limit (int, Optional, default=5): Number of in-stock items to return.
    
    LLM Usage & Instructions:
    1. Call this tool when the customer asks 'what do you recommend for me?' or wants general suggestions.
    2. If user_id is NOT provided (or user is a guest/unauthenticated):
       This tool automatically falls back to top store-wide best-sellers.
       You MUST present these recommendations and ALWAYS conclude your response with:
       "For personalized recommendations tailored specifically to your style and size, please log in or sign up to Dukaan!"
    """
    is_guest = user_id is None or user_id <= 0

    try:
        if is_guest:
            # Fall back to best sellers if no user_id is provided
            if product_type:
                raw_results = await recommedationController.recommedMostGoodProductByType(
                    product_type=product_type,
                    gender=gender,
                    limit=limit,
                )
            else:
                raw_results = await recommedationController.recommedMostGoodProduct(
                    gender=gender,
                    limit=limit,
                )
        else:
            raw_results = await recommedationController.recommedTheUserPorduct(
                user_id=user_id,
                gender=gender,
                product_type=product_type,
                limit=limit,
            )

        sanitized_items = []

        for item in raw_results:
            p = item.get("product")
            if p:
                sanitized_items.append({
                    "product_id": p.id,
                    "product": _sanitize_product(p),
                    "probability_score": item.get("score", 0.0),
                })

        # Track user events: VIEWED for recommended items only if user_id is provided (> 0)
        if not is_guest and user_id and sanitized_items:
            product_ids = [item["product_id"] for item in sanitized_items if item.get("product_id")]
            categories = {
                item["product_id"]: (item["product"].get("type") or product_type or "general")
                for item in sanitized_items
                if item.get("product_id")
            }
            await record_bulk_user_events(
                user_id=user_id,
                product_ids=product_ids,
                event_type=EventType.VIEWED,
                categories=categories,
            )

        return {
            "success": True,
            "count": len(sanitized_items),
            "products": sanitized_items,
            "requires_login_for_personalization": is_guest,
            "login_prompt": LOGIN_NUDGE_PROMPT if is_guest else None,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to fetch personalized recommendations: {str(e)}",
        }


@mcp.tool()
async def get_category_best_sellers(
    product_type: str,
    user_id: Optional[int] = None,
    gender: Optional[str] = None,
    limit: int = 5,
) -> Dict[str, Any]:
    """
    Retrieves the highest-ranked, top-converting in-stock products for a specific category.
    
    Parameters:
    - product_type (str, Required): One of 't-shirt', 'jeans', 'shirt', 'hoodie', 'short'.
    - user_id (int, Optional): Customer ID to record view preferences if authenticated.
    - gender (str, Optional): 'men', 'women', or 'unisex'.
    - limit (int, Optional, default=5): Number of items to return.
    
    LLM Usage & Instructions:
    - Use this tool when the customer asks for the best, most popular, or top-rated items in a category.
    - If the user is unauthenticated, remind them to log in or sign up for personalized suggestions.
    """
    try:
        raw_results = await recommedationController.recommedMostGoodProductByType(
            product_type=product_type,
            gender=gender,
            limit=limit,
        )

        sanitized_items = [
            {
                "product_id": item["product"].id,
                "product": _sanitize_product(item["product"]),
                "popularity_score": item.get("score", 0.0),
            }
            for item in raw_results
            if item.get("product")
        ]

        # Track user events: VIEWED for recommended items only if user_id is provided (> 0)
        if user_id and user_id > 0 and sanitized_items:
            product_ids = [item["product_id"] for item in sanitized_items if item.get("product_id")]
            categories = {
                item["product_id"]: (item["product"].get("type") or product_type or "general")
                for item in sanitized_items
                if item.get("product_id")
            }
            await record_bulk_user_events(
                user_id=user_id,
                product_ids=product_ids,
                event_type=EventType.VIEWED,
                categories=categories,
            )

        return {
            "success": True,
            "category": product_type,
            "count": len(sanitized_items),
            "products": sanitized_items,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to fetch category best sellers: {str(e)}",
        }


@mcp.tool()
async def get_global_best_sellers(
    user_id: Optional[int] = None,
    gender: Optional[str] = None,
    limit: int = 5,
) -> Dict[str, Any]:
    """
    Retrieves top-performing, most popular in-stock products across the entire Dukaan catalog.
    
    Parameters:
    - user_id (int, Optional): Customer ID to record view preferences if authenticated.
    - gender (str, Optional): 'men', 'women', or 'unisex'.
    - limit (int, Optional, default=5): Number of items to return.
    
    LLM Usage & Instructions:
    - Use when the user asks for trending items or overall store best-sellers.
    - If the user is browsing as a guest, remind them to log in or sign up to personalize their feed.
    """
    try:
        raw_results = await recommedationController.recommedMostGoodProduct(
            gender=gender,
            limit=limit,
        )

        sanitized_items = [
            {
                "product_id": item["product"].id,
                "product": _sanitize_product(item["product"]),
                "popularity_score": item.get("score", 0.0),
            }
            for item in raw_results
            if item.get("product")
        ]

        # Track user events: VIEWED for recommended items only if user_id is provided (> 0)
        if user_id and user_id > 0 and sanitized_items:
            product_ids = [item["product_id"] for item in sanitized_items if item.get("product_id")]
            categories = {
                item["product_id"]: (item["product"].get("type") or "general")
                for item in sanitized_items
                if item.get("product_id")
            }
            await record_bulk_user_events(
                user_id=user_id,
                product_ids=product_ids,
                event_type=EventType.VIEWED,
                categories=categories,
            )

        return {
            "success": True,
            "count": len(sanitized_items),
            "products": sanitized_items,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to fetch global best sellers: {str(e)}",
        }


# ==============================================================================
# LangChain / LangGraph Adapter Helper
# ==============================================================================

def get_recommendation_langchain_tools() -> List[StructuredTool]:
    """
    Returns the recommendation tools wrapped as native LangChain StructuredTool instances,
    ready to bind directly to LangGraph specialist agents without network overhead.
    """
    return [
        StructuredTool.from_function(
            coroutine=search_and_recommend_by_type,
            name="search_and_recommend_by_type",
            description=search_and_recommend_by_type.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=recommend_by_query,
            name="recommend_by_query",
            description=recommend_by_query.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=get_personalized_recommendations,
            name="get_personalized_recommendations",
            description=get_personalized_recommendations.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=get_category_best_sellers,
            name="get_category_best_sellers",
            description=get_category_best_sellers.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=get_global_best_sellers,
            name="get_global_best_sellers",
            description=get_global_best_sellers.__doc__,
        ),
    ]
