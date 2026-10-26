import asyncio
import os
import sys

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from Recommedation.tools import (
    search_and_recommend_by_type,
    recommend_by_query,
    get_personalized_recommendations,
    get_category_best_sellers,
    get_global_best_sellers,
)
from agents.user.graph import _build_cards_from_tool

FORBIDDEN_FIELDS = [
    "discount",
    "discount_percentage",
    "discount_percent",
    "min_selling_price",
    "minimum_selling_price",
    "min_price",
    "cost_price",
    "min_profit_margin_percent",
]


async def run_privacy_tests():
    print("=" * 60)
    print("RUNNING PRIVACY CHECKS ON RECOMMENDATION TOOLS")
    print("=" * 60)

    # 1. Test search_and_recommend_by_type
    res1 = await search_and_recommend_by_type(product_type="jeans", limit=3)
    assert res1.get("success"), f"search_and_recommend_by_type failed: {res1}"
    products1 = res1.get("products", [])
    print(f"[Check 1] search_and_recommend_by_type returned {len(products1)} items.")
    for item in products1:
        prod = item.get("product", {})
        for field in FORBIDDEN_FIELDS:
            assert field not in prod, f"Found forbidden field '{field}' in product {prod.get('id')}"
            assert field not in item, f"Found forbidden field '{field}' in item {item.get('product_id')}"
    print("  -> Passed: No confidential discount or minimum selling price fields present.")

    # 2. Test recommend_by_query
    res2 = await recommend_by_query(user_query="casual cotton t-shirt", limit=3)
    assert res2.get("success"), f"recommend_by_query failed: {res2}"
    products2 = res2.get("products", [])
    print(f"[Check 2] recommend_by_query returned {len(products2)} items.")
    for item in products2:
        prod = item.get("product", {})
        for field in FORBIDDEN_FIELDS:
            assert field not in prod, f"Found forbidden field '{field}' in product {prod.get('id')}"
            assert field not in item, f"Found forbidden field '{field}' in item {item.get('product_id')}"
    print("  -> Passed: No confidential discount or minimum selling price fields present.")

    # 3. Test get_category_best_sellers
    res3 = await get_category_best_sellers(product_type="shirt", limit=3)
    assert res3.get("success"), f"get_category_best_sellers failed: {res3}"
    products3 = res3.get("products", [])
    print(f"[Check 3] get_category_best_sellers returned {len(products3)} items.")
    for item in products3:
        prod = item.get("product", {})
        for field in FORBIDDEN_FIELDS:
            assert field not in prod, f"Found forbidden field '{field}' in product {prod.get('id')}"
            assert field not in item, f"Found forbidden field '{field}' in item {item.get('product_id')}"
    print("  -> Passed: No confidential discount or minimum selling price fields present.")

    # 4. Test get_global_best_sellers
    res4 = await get_global_best_sellers(limit=3)
    assert res4.get("success"), f"get_global_best_sellers failed: {res4}"
    products4 = res4.get("products", [])
    print(f"[Check 4] get_global_best_sellers returned {len(products4)} items.")
    for item in products4:
        prod = item.get("product", {})
        for field in FORBIDDEN_FIELDS:
            assert field not in prod, f"Found forbidden field '{field}' in product {prod.get('id')}"
            assert field not in item, f"Found forbidden field '{field}' in item {item.get('product_id')}"
    print("  -> Passed: No confidential discount or minimum selling price fields present.")

    # 5. Test _build_cards_from_tool for RecommendationCard UI payload
    cards = _build_cards_from_tool("search_and_recommend_by_type", res1, {}, {})
    assert len(cards) > 0, "No card produced from search_and_recommend_by_type"
    rec_card = cards[0]
    assert rec_card["type"] == "recommendation"
    card_prods = rec_card["data"]["products"]
    print(f"[Check 5] UI RecommendationCard contains {len(card_prods)} sanitized products.")
    for p in card_prods:
        for field in FORBIDDEN_FIELDS:
            assert field not in p, f"Found forbidden field '{field}' in UI card product {p.get('id')}"
    print("  -> Passed: UI card strictly excludes all forbidden fields.")

    print("=" * 60)
    print("ALL RECOMMENDATION PRIVACY CHECKS COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_privacy_tests())
