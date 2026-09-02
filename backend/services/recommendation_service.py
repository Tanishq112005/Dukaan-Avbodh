from models.product import Product, ProductType
from services.behavior_scorer import behavior_scorer
from repositories.product_repository import ProductRepository
from repositories.user_event_repository import UserEventRepository

product_repo = ProductRepository()
event_repo = UserEventRepository()

COMPLEMENTARY_CATEGORIES = {
    "t-shirt": ["jeans", "short"],
    "shirt": ["jeans", "short"],
    "hoodie": ["jeans", "short"],
    "jeans": ["t-shirt", "shirt", "hoodie"],
    "short": ["t-shirt", "shirt", "hoodie"],
}

FASHION_FLOW = ["hoodie", "t-shirt", "shirt", "short", "jeans"]
TOPS = {"shirt", "t-shirt", "hoodie"}
BOTTOMS = {"jeans", "short"}


def _minmax_norm(value: float, min_v: float, max_v: float) -> float:
    if max_v <= min_v:
        return 0.5
    return (value - min_v) / (max_v - min_v)


def _type_value(product: Product) -> str:
    return product.type.value if hasattr(product.type, "value") else str(product.type)


def _parse_types(names: list[str]) -> list[ProductType]:
    parsed = []
    for name in names:
        try:
            parsed.append(ProductType(name))
        except ValueError:
            continue
    return parsed


class RecommendationService:
    def hybrid_score(self, event_relevance: float, importance_score: float, rel_bounds: tuple[float, float], imp_bounds: tuple[float, float]) -> float:
        rel_n = _minmax_norm(event_relevance, rel_bounds[0], rel_bounds[1])
        imp_n = _minmax_norm(float(importance_score), imp_bounds[0], imp_bounds[1])
        return (rel_n * 0.5) + (imp_n * 0.5)

    def rank_products(
        self,
        products: list[Product],
        category_scores: dict[str, float],
        product_scores: dict[int, float],
        limit: int = 4,
    ) -> list[tuple[Product, float, float]]:
        if not products:
            return []

        relevances = []
        importances = []
        for product in products:
            cat = _type_value(product)
            relevance = category_scores.get(cat, 0.0) + product_scores.get(product.id, 0.0)
            relevances.append(relevance)
            importances.append(float(product.importance_score or 0))

        rel_bounds = (min(relevances), max(relevances))
        imp_bounds = (min(importances), max(importances))

        ranked = []
        for product, relevance, importance in zip(products, relevances, importances):
            score = self.hybrid_score(relevance, importance, rel_bounds, imp_bounds)
            ranked.append((product, score, relevance))

        ranked.sort(key=lambda row: (row[1], row[0].importance_score or 0, row[2]), reverse=True)
        return ranked[:limit]

    def rerank_search_hits(
        self,
        hits: list[tuple[Product, float]],
        semantic_keep_ratio: float = 0.55,
        semantic_floor: float = 0.25,
        limit: int = 4,
    ) -> list[tuple[Product, float, float]]:
        """Keep high semantic matches, then blend in importance without promoting off-query inventory."""
        if not hits:
            return []

        top_semantic = max(score for _, score in hits)
        floor = max(semantic_floor, top_semantic * semantic_keep_ratio)
        eligible = [(product, sem) for product, sem in hits if sem >= floor]
        if not eligible:
            eligible = sorted(hits, key=lambda row: row[1], reverse=True)[:limit]

        semantics = [sem for _, sem in eligible]
        importances = [float(p.importance_score or 0) for p, _ in eligible]
        sem_bounds = (min(semantics), max(semantics))
        imp_bounds = (min(importances), max(importances))

        ranked = []
        for product, semantic in eligible:
            sem_n = _minmax_norm(semantic, sem_bounds[0], sem_bounds[1])
            imp_n = _minmax_norm(float(product.importance_score or 0), imp_bounds[0], imp_bounds[1])
            combined = (sem_n * 0.7) + (imp_n * 0.3)
            ranked.append((product, combined, semantic))

        ranked.sort(key=lambda row: (row[2], row[1]), reverse=True)
        ranked.sort(key=lambda row: row[1], reverse=True)
        return ranked[:limit]

    def complementary_categories(self, cart_categories: set[str]) -> list[str]:
        if not cart_categories:
            return []
        targets: set[str] = set()
        for category in cart_categories:
            targets.update(COMPLEMENTARY_CATEGORIES.get(category, []))
        targets -= cart_categories
        if targets:
            return list(targets)
        if cart_categories.intersection(TOPS) and not cart_categories.intersection(BOTTOMS):
            return ["jeans", "short"]
        if cart_categories.intersection(BOTTOMS) and not cart_categories.intersection(TOPS):
            return ["shirt", "t-shirt"]
        return [cat for cat in FASHION_FLOW if cat not in cart_categories] or list(cart_categories)

    async def _target_categories(self, user_id: int, cart_items: list[dict], category_scores: dict[str, float]) -> list[str]:
        cart_categories = {item.get("type") or item.get("category") for item in cart_items}
        cart_categories = {c for c in cart_categories if c}

        if cart_categories:
            return self.complementary_categories(cart_categories)

        user_events = await event_repo.get_events_for_user(user_id)
        viewed = behavior_scorer.top_viewed_categories(user_events, limit=3)
        affinity = sorted(category_scores, key=category_scores.get, reverse=True)
        merged = []
        for category in viewed + affinity:
            if category and category not in merged:
                merged.append(category)
        return merged[:3] or ["jeans"]

    async def get_best_suggestion(self, user_id: int, cart_items: list[dict], limit: int = 4) -> list[Product]:
        category_scores, product_scores = await behavior_scorer.get_affinity_maps(user_id)
        target_categories = await self._target_categories(user_id, cart_items, category_scores)
        parsed_types = _parse_types(target_categories)

        cart_ids = {item.get("id") or item.get("product_id") for item in cart_items}

        candidates = await product_repo.get_in_stock_by_types(parsed_types) if parsed_types else []
        candidates = [p for p in candidates if p.id not in cart_ids]

        cart_genders = [item.get("gender") for item in cart_items if item.get("gender")]
        if cart_genders:
            target_gender = max(set(cart_genders), key=cart_genders.count)
        else:
            target_gender = await behavior_scorer.get_current_gender_context(user_id)

        if target_gender and target_gender != "unisex":
            gendered = [p for p in candidates if not p.gender or p.gender in (target_gender, "unisex")]
            if gendered:
                candidates = gendered

        if not candidates:
            fallback = await product_repo.get_in_stock()
            candidates = [p for p in fallback if p.id not in cart_ids]

        ranked = self.rank_products(candidates, category_scores, product_scores, limit=limit)
        return [product for product, _, _ in ranked]


recommendation_service = RecommendationService()
