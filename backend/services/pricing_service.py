from typing import Any, Dict, List, Optional

from models import Campaign, Product
from repositories.campain_repository import CampaignRepository
from utils.pricing_math import apply_sequential_discounts

campaign_repo = CampaignRepository()


def _campaign_type_value(campaign: Campaign) -> str:
    ctype = campaign.type
    return ctype.value if hasattr(ctype, "value") else str(ctype)


def serialize_campaign(campaign: Campaign) -> Dict[str, Any]:
    return {
        "campaign_id": campaign.id,
        "agenda": campaign.agenda,
        "discount_percentage": campaign.discount_percentage,
        "type": _campaign_type_value(campaign),
        "priority": campaign.priority or 0,
    }


def sort_campaigns_for_stacking(campaigns: List[Campaign]) -> List[Campaign]:
    return sorted(
        campaigns,
        key=lambda c: (-(c.priority or 0), -float(c.discount_percentage or 0), c.id or 0),
    )


class PricingService:
    """
    Sequential campaign discounts become the product's New Selling Price.
    All combo, search, and negotiation math must use that NSP going forward.
    """

    def price_from_campaigns(
        self,
        product: Product,
        campaigns: Optional[List[Campaign]] = None,
        quantity: int = 1,
    ) -> Dict[str, Any]:
        stacked = sort_campaigns_for_stacking(campaigns or [])
        percents = [c.discount_percentage for c in stacked if c.discount_percentage]
        nsp = apply_sequential_discounts(product.price, percents) if percents else round(float(product.price), 2)
        qty = max(1, int(quantity or 1))
        return {
            "id": product.id,
            "name": product.name,
            "image": product.image_url,
            "image_url": product.image_url,
            "type": product.type.value if hasattr(product.type, "value") else product.type,
            "gender": product.gender,
            "price": round(float(product.price), 2),
            "new_selling_price": nsp,
            "line_total": round(nsp * qty, 2),
            "cost_price": round(float(product.cost_price or 0.0), 2),
            "min_profit_margin_percent": float(product.min_profit_margin_percent or 0.0),
            "importance_score": int(product.importance_score or 0),
            "quantity": qty,
            "applied_campaigns": [serialize_campaign(c) for c in stacked if c.discount_percentage],
            "has_campaign": bool(percents),
        }

    async def price_products(
        self,
        products: List[Product],
        quantities: Optional[Dict[int, int]] = None,
    ) -> List[Dict[str, Any]]:
        if not products:
            return []
        ids = [p.id for p in products if p.id is not None]
        campaign_map = await campaign_repo.get_campaigns_by_product_ids(ids)
        qty_map = quantities or {}
        return [
            self.price_from_campaigns(p, campaign_map.get(p.id, []), qty_map.get(p.id, 1))
            for p in products
        ]

    async def price_cart_items(self, cart_items: List[dict]) -> List[Dict[str, Any]]:
        from repositories.product_repository import ProductRepository

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
