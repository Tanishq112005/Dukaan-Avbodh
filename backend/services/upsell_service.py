from services.recommendation_service import recommendation_service
from services.combo_pricing_engine import combo_pricing_engine
from services.pricing_service import pricing_service
from repositories.product_repository import ProductRepository

product_repo = ProductRepository()

SAFE_EXCLUDE = {"cost_price", "min_profit_margin_percent", "stock", "discount"}


class UpsellService:
    """Builds a curated kit: 1-2 cart items + 1-2 recommendations, priced at New Selling Price."""

    async def generate_upsell_offer(self, user_id: int, cart_items: list[dict]) -> dict:
        suggested_products = await recommendation_service.get_best_suggestion(user_id, cart_items)
        if not suggested_products:
            return {"success": False, "message": "No suitable recommendations found."}

        cart_ids = [item.get("id") or item.get("product_id") for item in cart_items]
        cart_ids = [int(i) for i in cart_ids if i is not None]
        cart_products = await product_repo.get_by_ids(cart_ids) if cart_ids else []

        quantities = {}
        for item in cart_items:
            pid = item.get("id") or item.get("product_id")
            if pid is None:
                continue
            quantities[int(pid)] = quantities.get(int(pid), 0) + int(item.get("quantity") or 1)

        cart_priced = await pricing_service.price_products(cart_products, quantities)
        rec_priced = await pricing_service.price_products(suggested_products)
        kit = combo_pricing_engine.build_kit(cart_priced, rec_priced)
        combo_offer = combo_pricing_engine.calculate_combo_price(kit)

        public_suggestions = []
        priced_by_id = {row["id"]: row for row in rec_priced}
        for product in suggested_products:
            payload = product.model_dump(exclude=SAFE_EXCLUDE)
            snapshot = priced_by_id.get(product.id)
            if snapshot:
                payload["new_selling_price"] = snapshot["new_selling_price"]
                payload["applied_campaigns"] = snapshot["applied_campaigns"]
                payload["has_campaign"] = snapshot["has_campaign"]
            public_suggestions.append(payload)

        return {
            "success": True,
            "suggested_products": public_suggestions,
            "combo_offer": combo_offer,
            "kit_products": kit,
        }


upsell_service = UpsellService()
