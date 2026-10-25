import logging
from typing import Optional, Dict, Any, List

from config.embeddingModel import embeddingModel
from config.vectorDatabase import vectorDB
from Recommedation.database import (
    RecommendationDatabase,
    recommendation_db,
)
from Recommedation.similarity import calculate_cosine_similarity

logger = logging.getLogger(__name__)


class Recommedation:
    """
    Recommendation Controller.
    Dependencies (db layer, embedder, and vector_db) are injected via __init__.
    Every public method returns a list of 4 to 5 recommended products.
    """

    def __init__(
        self,
        db: Optional[RecommendationDatabase] = None,
        embedder: Optional[Any] = None,
        vector_db: Optional[Any] = None,
    ):
        self.db = db or recommendation_db
        self._embedder = embedder
        self._vector_db = vector_db

    @property
    def embedder(self):
        if self._embedder is None:
            self._embedder = embeddingModel.getModel()
        return self._embedder

    @property
    def vector_db(self):
        if self._vector_db is None:
            self._vector_db = vectorDB
        return self._vector_db

    # ======================================================================
    # Internal Modular Helper Methods
    # ======================================================================

    def _encode_query(self, query: str) -> List[float]:
        """Encodes user query into a 384-dimensional dense vector."""
        vec = self.embedder.encode(query)
        if hasattr(vec, "tolist"):
            return vec.tolist()
        return list(vec)

    def _build_product_text(self, product) -> str:
        """Constructs a clean multi-line descriptive text for product matching."""
        category = (
            product.type.value
            if hasattr(product.type, "value")
            else str(product.type)
        )
        parts = [
            product.name,
            category,
            product.brand or "",
            product.description or "",
        ]
        return " ".join(filter(None, parts))

    def _query_pinecone_index(
        self,
        query_vector: List[float],
        gender: Optional[str] = None,
        top_k: int = 25,
    ):
        """Queries Pinecone index with strict gender metadata pre-filtering."""
        index = self.vector_db.get_index("dukaan-products")

        filter_dict = {}
        if gender:
            g_clean = gender.strip().lower()
            filter_dict["gender"] = {
                "$in": [
                    g_clean,
                    g_clean.capitalize(),
                    "unisex",
                    "Unisex",
                ]
            }

        return index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict if filter_dict else None,
        )

    def _rank_pinecone_candidates(
        self,
        matches,
        db_records: Dict[int, Dict[str, Any]],
        query: str,
        gender: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Calculates blended rank scores for matches returned by Pinecone."""
        ranked_products = []
        target_gender = gender.strip().lower() if gender else None

        for match in matches:
            if not str(match.id).isdigit():
                continue

            product_id = int(match.id)
            if product_id not in db_records:
                continue

            prod_info = db_records[product_id]
            product = prod_info["product"]

            # Strict gender validation guard
            if target_gender:
                prod_gender = (product.gender or "").strip().lower()
                if prod_gender and prod_gender not in (target_gender, "unisex"):
                    continue

            user_probability = prod_info["score"]
            cosine_sim = max(0.0, float(match.score or 0.0))

            # Bonus if product type matches query keyword
            product_type = str(getattr(product.type, "value", product.type)).lower()
            type_bonus = 0.2 if product_type in query else 0.0

            # Composite rank: 70% Pinecone Cosine Sim + 30% User Probability + Bonus
            rank_score = (
                (0.7 * cosine_sim)
                + (0.3 * user_probability)
                + type_bonus
            )

            ranked_products.append({
                "product_id": product.id,
                "product": product,
                "cosine_similarity": round(cosine_sim, 4),
                "probability_score": user_probability,
                "rank_score": round(rank_score, 4),
                "source": "pinecone_vector_db",
            })

        ranked_products.sort(
            key=lambda x: x["rank_score"],
            reverse=True,
        )
        return ranked_products

    async def _run_fallback_local_search(
        self,
        user_id: int,
        gender: Optional[str],
        query: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Fallback local search if Vector DB returns no matches or is in Dummy mode."""
        logger.info("Executing database candidate fallback search.")

        candidates = await self.db.get_candidates_for_query(
            user_id=user_id,
            gender=gender,
            limit=30,
        )
        if not candidates:
            return []

        product_texts = [
            self._build_product_text(c["product"])
            for c in candidates
        ]

        # Batch encode with local embedding model
        all_embeddings = self.embedder.encode([query] + product_texts)
        sim_scores = calculate_cosine_similarity(
            all_embeddings[0],
            all_embeddings[1:],
        )

        ranked = []
        for item, sim in zip(candidates, sim_scores):
            product = item["product"]
            user_prob = item["score"]

            prod_type = str(getattr(product.type, "value", product.type)).lower()
            type_bonus = 0.2 if prod_type in query else 0.0

            rank = (
                (0.7 * sim)
                + (0.3 * user_prob)
                + type_bonus
            )

            ranked.append({
                "product_id": product.id,
                "product": product,
                "cosine_similarity": round(sim, 4),
                "probability_score": user_prob,
                "rank_score": round(rank, 4),
                "source": "inhouse_fallback",
            })

        ranked.sort(
            key=lambda x: x["rank_score"],
            reverse=True,
        )
        return ranked[:limit]

    # ======================================================================
    # Public Recommendation API Methods
    # ======================================================================

    # 1. 4-5 best products for user (ProbabilityOfShowingItemsForParticularUser)
    async def recommedTheUserPorduct(
        self,
        user_id: int,
        gender: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Finds top 4-5 products for a user by score & gender (fallback to global)."""
        return await self.db.get_user_best_products(
            user_id=user_id,
            gender=gender,
            limit=limit,
        )

    # 2. 4-5 products through query + user probability via Vector DB (Pinecone)
    async def recommedTheUserProductThroughQuery(
        self,
        user_id: int,
        gender: Optional[str] = None,
        user_query: str = "",
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Encodes ONLY the query string, queries the Pinecone Vector Database,
        blends Cosine Similarity with the user's score, and returns top 4-5 products.
        """
        cleaned_query = user_query.strip().lower()

        # Step 1: Encode query to dense vector
        query_vector = self._encode_query(cleaned_query)

        # Step 2: Query Pinecone Vector Database with strict gender filter
        response = self._query_pinecone_index(
            query_vector=query_vector,
            gender=gender,
            top_k=25,
        )
        matches = getattr(response, "matches", []) or []

        # Step 3: Fetch matching product records and compute blended ranking
        if matches:
            product_ids = [
                int(m.id)
                for m in matches
                if str(m.id).isdigit()
            ]

            db_records = await self.db.get_products_by_ids_with_user_scores(
                product_ids=product_ids,
                user_id=user_id,
                gender=gender,
            )

            ranked_products = self._rank_pinecone_candidates(
                matches=matches,
                db_records=db_records,
                query=cleaned_query,
                gender=gender,
            )
            if ranked_products:
                return ranked_products[:limit]

        # Step 4: Fallback to local DB candidate search if Vector DB had no matches
        return await self._run_fallback_local_search(
            user_id=user_id,
            gender=gender,
            query=cleaned_query,
            limit=limit,
        )

    # 3. Overall top 4-5 products (ProbabilityOfShowingItems)
    async def recommedMostGoodProduct(
        self,
        gender: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Finds top 4-5 products globally from ProbabilityOfShowingItems."""
        return await self.db.get_most_good_products_global(
            gender=gender,
            limit=limit,
        )

    # 4. Top 4-5 products by product type (ProbabilityOfShowingItems)
    async def recommedMostGoodProductByType(
        self,
        product_type: str,
        gender: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Finds top 4-5 products of a given type from ProbabilityOfShowingItems."""
        return await self.db.get_most_good_products_by_type(
            product_type=product_type,
            gender=gender,
            limit=limit,
        )

    # Naming aliases for backwards compatibility
    recommedTheUserProduct = recommedTheUserPorduct
    getMostGoodProduct = recommedMostGoodProduct
    getMostGoodProductByType = recommedMostGoodProductByType


# Exported instances
recommedationController = Recommedation(
    db=recommendation_db,
    vector_db=vectorDB,
)
recommendationController = recommedationController
