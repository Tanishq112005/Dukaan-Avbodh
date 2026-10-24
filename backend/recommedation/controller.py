import logging
from typing import Optional, Dict, Any, List

from config.embeddingModel import embeddingModel
from recommedation.database import RecommendationDatabase, recommendation_db
from recommedation.similarity import calculate_cosine_similarity

logger = logging.getLogger(__name__)


class Recommedation:
    """
    Recommendation Controller class.
    Dependencies (db layer and embedder model) are injected via __init__.
    Every method returns a list of 4 to 5 recommended products.
    """

    def __init__(
        self,
        db: Optional[RecommendationDatabase] = None,
        embedder: Optional[Any] = None,
    ):
        self.db = db or recommendation_db
        self._embedder = embedder

    @property
    def embedder(self):
        if self._embedder is None:
            self._embedder = embeddingModel.getModel()
        return self._embedder

    # ----------------------------------------------------------------------
    # 1. 4-5 best products for user (ProbabilityOfShowingItemsForParticularUser)
    # ----------------------------------------------------------------------
    async def recommedTheUserPorduct(
        self, user_id: int, gender: Optional[str] = None, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Finds top 4-5 products for a user by score & gender (fallback to global)."""
        return await self.db.get_user_best_products(
            user_id=user_id, gender=gender, limit=limit
        )

    # ----------------------------------------------------------------------
    # 2. 4-5 products through query + user probability via Transformer & Cosine Sim
    # ----------------------------------------------------------------------
    async def recommedTheUserProductThroughQuery(
        self,
        user_id: int,
        gender: Optional[str] = None,
        user_query: str = "",
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Encodes query and candidate products with the Transformer model,
        computes Cosine Similarity using library cos_sim, blends with user probability,
        and returns the top 4-5 ranked products.
        """
        candidates = await self.db.get_candidates_for_query(
            user_id=user_id, gender=gender, limit=50
        )
        if not candidates:
            return []

        q_clean = user_query.strip().lower()

        # Build product texts
        product_texts = [
            f"{c['product'].name} {getattr(c['product'].type, 'value', c['product'].type)} {c['product'].brand or ''} {c['product'].description or ''}"
            for c in candidates
        ]

        # Batch encode with Transformer model
        all_embeddings = self.embedder.encode([q_clean] + product_texts)
        q_vec = all_embeddings[0]
        p_matrix = all_embeddings[1:]

        # Library cosine similarity
        sim_scores = calculate_cosine_similarity(q_vec, p_matrix)

        # Rank candidates: 70% Cosine Similarity + 30% User Probability + Type Bonus
        ranked = []
        for item, sim in zip(candidates, sim_scores):
            prod = item["product"]
            user_prob = item["score"]
            prod_type = str(getattr(prod.type, "value", prod.type)).lower()

            type_bonus = 0.2 if prod_type in q_clean else 0.0
            rank = (0.7 * sim) + (0.3 * user_prob) + type_bonus

            ranked.append({
                "product_id": prod.id,
                "product": prod,
                "cosine_similarity": round(sim, 4),
                "probability_score": user_prob,
                "rank_score": round(rank, 4),
            })

        # Sort descending by rank and return top 4-5
        ranked.sort(key=lambda x: x["rank_score"], reverse=True)
        return ranked[:limit]

    # ----------------------------------------------------------------------
    # 3. Overall top 4-5 products (ProbabilityOfShowingItems)
    # ----------------------------------------------------------------------
    async def recommedMostGoodProduct(
        self, gender: Optional[str] = None, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Finds top 4-5 products globally from ProbabilityOfShowingItems."""
        return await self.db.get_most_good_products_global(
            gender=gender, limit=limit
        )

    # ----------------------------------------------------------------------
    # 4. Top 4-5 products by product type (ProbabilityOfShowingItems)
    # ----------------------------------------------------------------------
    async def recommedMostGoodProductByType(
        self, product_type: str, gender: Optional[str] = None, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Finds top 4-5 products of a given type from ProbabilityOfShowingItems."""
        return await self.db.get_most_good_products_by_type(
            product_type=product_type, gender=gender, limit=limit
        )

    # Naming aliases for compatibility
    recommedTheUserProduct = recommedTheUserPorduct
    getMostGoodProduct = recommedMostGoodProduct
    getMostGoodProductByType = recommedMostGoodProductByType


recommedationController = Recommedation(db=recommendation_db)
recommendationController = recommedationController
