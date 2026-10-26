from typing import Any, Dict, List, Optional
from Product.models import Product
from utils.pricing_math import apply_sequential_discounts


def _campaign_type_value(campaign: Any) -> str:
    ctype = getattr(campaign, "type", "low_priority")
    return ctype.value if hasattr(ctype, "value") else str(ctype)


def serialize_campaign(campaign: Any) -> Dict[str, Any]:
    return {
        "campaign_id": getattr(campaign, "id", None),
        "agenda": getattr(campaign, "agenda", ""),
        "discount_percentage": getattr(campaign, "discount_percentage", 0.0),
        "type": _campaign_type_value(campaign),
        "priority": getattr(campaign, "priority", 0) or 0,
    }


def sort_campaigns_for_stacking(campaigns: List[Any]) -> List[Any]:
    return sorted(
        campaigns or [],
        key=lambda c: (-(getattr(c, "priority", 0) or 0), -float(getattr(c, "discount_percentage", 0.0) or 0), getattr(c, "id", 0) or 0),
    )


class PricingService:
    """
    Sequential campaign discounts become the product's New Selling Price.
    All combo, search, and negotiation math must use that NSP going forward.
    """

    def price_from_campaigns(
        self,
        product: Product,
        campaigns: Optional[List[Any]] = None,
        quantity: int = 1,
    ) -> Dict[str, Any]:
        stacked = sort_campaigns_for_stacking(campaigns or [])
        percents = [getattr(c, "discount_percentage", 0) for c in stacked if getattr(c, "discount_percentage", 0)]
        nsp = apply_sequential_discounts(product.price, percents) if percents else round(float(product.price), 2)
        qty = max(1, int(quantity or 1))
        return {
            "id": product.id,
            "name": product.name,
            "image": getattr(product, "image_url", None),
            "image_url": getattr(product, "image_url", None),
            "type": product.type.value if hasattr(product.type, "value") else str(product.type),
            "price": round(float(product.price), 2),
            "new_selling_price": nsp,
            "importance_score": int(getattr(product, "importance_score", 0) or 0),
            "quantity": qty,
            "applied_campaigns": [serialize_campaign(c) for c in stacked if getattr(c, "discount_percentage", 0)],
            "has_campaign": bool(percents),
        }

    async def price_products(
        self,
        products: List[Product],
        quantities: Optional[Dict[int, int]] = None,
    ) -> List[Dict[str, Any]]:
        if not products:
            return []
        qty_map = quantities or {}
        return [
            self.price_from_campaigns(p, [], qty_map.get(p.id, 1))
            for p in products
        ]

    async def price_cart_items(self, cart_items: List[dict]) -> List[Dict[str, Any]]:
        from Product.database import ProductRepository

        product_repo = ProductRepository()
        ids = [item.get("id") or item.get("product_id") for item in cart_items]
        ids = [int(i) for i in ids if i is not None]
        products = await product_repo.get_by_ids(ids)
        by_id = {p.id: p for p in products}
        quantities = {}
        for item in cart_items:
            pid = item.get("id") or item.get("product_id")
            if pid is None:
                continue
            quantities[int(pid)] = quantities.get(int(pid), 0) + int(item.get("quantity") or 1)
        ordered = [by_id[pid] for pid in quantities if pid in by_id]
        return await self.price_products(ordered, quantities)

    def public_product_fields(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": snapshot["id"],
            "name": snapshot["name"],
            "image": snapshot.get("image"),
            "image_url": snapshot.get("image_url"),
            "type": snapshot.get("type"),
            "price": snapshot["price"],
            "new_selling_price": snapshot["new_selling_price"],
            "quantity": snapshot.get("quantity", 1),
            "applied_campaigns": snapshot.get("applied_campaigns", []),
            "has_campaign": snapshot.get("has_campaign", False),
        }


pricing_service = PricingService()
