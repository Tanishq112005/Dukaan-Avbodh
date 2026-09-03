from typing import Any, Dict, List


class ComboPricingEngine:
    """
    Prices a curated kit from New Selling Prices (campaign-stacked).
    Negotiation limits are computed against NSP, never the pre-campaign list price.
    """

    COMBO_BONUS_PERCENT = 5.0

    def get_negotiation_limits(self, priced_items: List[Dict[str, Any]]) -> dict:
        total_price = sum(float(p.get("new_selling_price", p.get("price", 0))) * int(p.get("quantity", 1)) for p in priced_items)
        total_cost = sum(float(p.get("cost_price", 0)) * int(p.get("quantity", 1)) for p in priced_items)
        total_min_profit = sum(
            float(p.get("cost_price", 0)) * (float(p.get("min_profit_margin_percent", 0)) / 100) * int(p.get("quantity", 1))
            for p in priced_items
        )

        margin = total_price - total_cost
        max_discount_amount = total_price - total_cost - total_min_profit
        absolute_max_discount_percent = (max_discount_amount / total_price) * 100 if total_price > 0 else 0.0
        absolute_max_discount_percent = max(0.0, absolute_max_discount_percent)

        return {
            "total_price": round(total_price, 2),
            "total_cost": round(total_cost, 2),
            "total_min_profit": round(total_min_profit, 2),
            "margin": round(margin, 2),
            "max_discount_amount": round(max_discount_amount, 2),
            "absolute_max_discount_percent": round(absolute_max_discount_percent, 2),
            "loss_leader": margin <= 0,
        }

    def calculate_combo_price(self, priced_items: List[Dict[str, Any]], discount_percent: float = 0.0) -> dict:
        if not priced_items:
            return {
                "subtotal": 0.0,
                "total_combo_price": 0.0,
                "final_price": 0.0,
                "effective_discount_percent": 0.0,
                "extra_discount_percent": 0.0,
                "discount_amount": 0.0,
                "campaign_savings": 0.0,
                "total_items": 0,
                "products": [],
                "applied_campaigns": [],
                "has_campaign": False,
            }

        subtotal_base = sum(float(p["price"]) * int(p.get("quantity", 1)) for p in priced_items)
        total_combo_price = sum(float(p["new_selling_price"]) * int(p.get("quantity", 1)) for p in priced_items)
        campaign_savings = round(subtotal_base - total_combo_price, 2)
        discount_amount = round(total_combo_price * (max(0.0, discount_percent) / 100), 2)
        final_price = round(total_combo_price - discount_amount, 2)

        campaigns = []
        seen = set()
        for item in priced_items:
            for campaign in item.get("applied_campaigns") or []:
                cid = campaign.get("campaign_id")
                if cid in seen:
                    continue
                seen.add(cid)
                campaigns.append(campaign)

        extra_discount_percent = round(max(0.0, float(discount_percent or 0.0)), 2)
        campaign_discount_percent = ((subtotal_base - total_combo_price) / subtotal_base * 100) if subtotal_base > 0 else 0.0
        overall_discount_percent = ((subtotal_base - final_price) / subtotal_base * 100) if subtotal_base > 0 else 0.0

        return {
            "subtotal": round(subtotal_base, 2),
            "total_combo_price": round(total_combo_price, 2),
            "final_price": final_price,
            "extra_discount_percent": extra_discount_percent,
            "effective_discount_percent": round(overall_discount_percent, 2),
            "campaign_discount_percent": round(campaign_discount_percent, 2),
            "discount_amount": discount_amount,
            "campaign_savings": campaign_savings,
            "total_items": sum(int(p.get("quantity", 1)) for p in priced_items),
            "products": [
                {
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "image": p.get("image") or p.get("image_url"),
                    "price": p.get("price"),
                    "new_selling_price": p.get("new_selling_price"),
                    "quantity": p.get("quantity", 1),
                    "applied_campaigns": p.get("applied_campaigns", []),
                    "source": p.get("source"),
                }
                for p in priced_items
            ],
            "applied_campaigns": campaigns,
            "has_campaign": any(p.get("has_campaign") for p in priced_items),
        }

    def build_kit(self, cart_priced: List[Dict[str, Any]], recommended_priced: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """1-2 cart items + 1-2 recommended items. Campaign items are preferred in each bucket."""
        def pick(items: List[Dict[str, Any]], limit: int, source: str) -> List[Dict[str, Any]]:
            ordered = sorted(
                items,
                key=lambda p: (
                    1 if p.get("has_campaign") else 0,
                    p.get("importance_score") or 0,
                    p.get("new_selling_price") or 0,
                ),
                reverse=True,
            )
            chosen = []
            seen = set()
            for item in ordered:
                if item.get("id") in seen:
                    continue
                snapshot = dict(item)
                snapshot["source"] = source
                chosen.append(snapshot)
                seen.add(item.get("id"))
                if len(chosen) >= limit:
                    break
            return chosen

        cart_pick = pick(cart_priced, 2, "cart")
        cart_ids = {p["id"] for p in cart_pick}
        rec_pool = [p for p in recommended_priced if p.get("id") not in cart_ids]
        rec_pick = pick(rec_pool, 2, "recommended")
        kit = cart_pick + rec_pick
        if len(kit) < 2 and rec_pool:
            for extra in rec_pool:
                if extra.get("id") not in {p["id"] for p in kit}:
                    snapshot = dict(extra)
                    snapshot["source"] = "recommended"
                    kit.append(snapshot)
                if len(kit) >= 2:
                    break
        return kit


combo_pricing_engine = ComboPricingEngine()
