import logging
from typing import Optional, Dict, Any, List, Union

from config.embeddingModel import embeddingModel
from config.vectorDatabase import vectorDB
from Product.models import ProductType
from Recommedation.database import (
    RecommendationDatabase,
    recommendation_db,
    resolve_product_type,
)
from Recommedation.similarity import calculate_cosine_similarity

logger = logging.getLogger(__name__)


class Recommedation:
    """
    Recommendation Controller.
    Strictly recommends ONLY products with active stock (stock > 0).
    If top-ranked items are out of stock, the algorithm automatically skips them
    and retrieves the next in-stock products according to ranking and score.
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
        product_type: Optional[str] = None,
        top_k: int = 50,
    ):
        """
        Queries Pinecone index with strict gender and product type metadata pre-filtering.
        Uses top_k=50 to ensure abundant candidates even if some top matches are out of stock.
        """
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

        if product_type:
            resolved_pt = resolve_product_type(product_type)
            categories = []
            if resolved_pt:
                categories.extend([
                    resolved_pt.value,
                    resolved_pt.value.capitalize(),
                    resolved_pt.name,
                    resolved_pt.name.lower(),
                ])
            else:
                pt_clean = str(getattr(product_type, "value", product_type)).strip().lower()
                categories.extend([pt_clean, pt_clean.capitalize(), pt_clean.upper()])

            filter_dict["category"] = {"$in": list(set(categories))}

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
        product_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Calculates blended rank scores for matches returned by Pinecone.
        Strictly filters out any products with stock <= 0, and filters by product_type if provided.
        """
        ranked_products = []
        target_gender = gender.strip().lower() if gender else None
        target_type = resolve_product_type(product_type)

        for match in matches:
            if not str(match.id).isdigit():
                continue

            product_id = int(match.id)
            if product_id not in db_records:
                continue

            prod_info = db_records[product_id]
            product = prod_info["product"]

            # Strict in-stock validation: skip if out of stock
            if not product or not getattr(product, "stock", 0) or product.stock <= 0:
                continue

            # Strict product type validation guard
            if target_type:
                prod_type_enum = resolve_product_type(product.type)
                if prod_type_enum != target_type:
                    continue

            # Strict gender validation guard
            if target_gender:
                prod_gender = (product.gender or "").strip().lower()
                if prod_gender and prod_gender not in (target_gender, "unisex"):
                    continue

            user_probability = prod_info["score"]
            cosine_sim = max(0.0, float(match.score or 0.0))

            # Bonus if product type matches query keyword
            p_type_str = str(getattr(product.type, "value", product.type)).lower()
            type_bonus = 0.2 if p_type_str in query else 0.0

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
        product_type: Optional[str] = None,
        exclude_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fallback local search when Vector DB has insufficient in-stock items.
        Strictly evaluates only products with stock > 0 and matching type.
        """
        logger.info("Executing database candidate fallback search for next in-stock items.")

        candidates = await self.db.get_candidates_for_query(
            user_id=user_id,
            gender=gender,
            product_type=product_type,
            limit=50,
            exclude_ids=exclude_ids,
        )
        if not candidates:
            return []

        # Filter strictly for products with stock > 0
        valid_candidates = [
            c for c in candidates
            if c.get("product") and getattr(c["product"], "stock", 0) and c["product"].stock > 0
        ]
        if not valid_candidates:
            return []

        if product_type:
            target_pt = resolve_product_type(product_type)
            if target_pt:
                valid_candidates = [
                    c for c in valid_candidates
                    if resolve_product_type(c["product"].type) == target_pt
                ]
            if not valid_candidates:
                return []

        clean_query = (query or "").strip().lower()
        if not clean_query and product_type:
            clean_query = str(getattr(product_type, "value", product_type)).strip().lower()

        if not clean_query:
            # Sort directly by user probability score
            valid_candidates.sort(key=lambda x: x["score"], reverse=True)
            return [
                {
                    "product_id": c["product"].id,
                    "product": c["product"],
                    "cosine_similarity": 0.0,
                    "probability_score": c["score"],
                    "rank_score": round(c["score"], 4),
                    "source": "inhouse_fallback",
                }
                for c in valid_candidates[:limit]
            ]

        product_texts = [
            self._build_product_text(c["product"])
            for c in valid_candidates
        ]

        # Batch encode with local embedding model
        all_embeddings = self.embedder.encode([clean_query] + product_texts)
        sim_scores = calculate_cosine_similarity(
            all_embeddings[0],
            all_embeddings[1:],
        )

        ranked = []
        for item, sim in zip(valid_candidates, sim_scores):
            product = item["product"]
            user_prob = item["score"]

            prod_type = str(getattr(product.type, "value", product.type)).lower()
            type_bonus = 0.2 if prod_type in clean_query else 0.0

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

    # 1. Best products for user (ProbabilityOfShowingItemsForParticularUser + next in-stock backfill)
    async def recommedTheUserPorduct(
        self,
        user_id: int,
        gender: Optional[str] = None,
        product_type: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Finds top in-stock products for a user by personalized score, gender & type.
        If any top products are out of stock, automatically skips them and fetches
        the next in-stock products according to ranking.
        """
        return await self.db.get_user_best_products(
            user_id=user_id,
            gender=gender,
            product_type=product_type,
            limit=limit,
        )

    # 2. Products through query + user probability via Vector DB (with next in-stock backfill)
    async def recommedTheUserProductThroughQuery(
        self,
        user_id: int,
        gender: Optional[str] = None,
        user_query: str = "",
        product_type: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Encodes query string, queries Pinecone Vector Database, blends Cosine Similarity
        with user score, and strictly returns only in-stock products.
        Supports filtering by product_type and gender.
        If top-matched items are out of stock, skips them and fetches the next in-stock items.
        """
        cleaned_query = (user_query or "").strip().lower()

        # If user_query is empty, fallback to product_type text if provided
        effective_query = cleaned_query
        if not effective_query and product_type:
            effective_query = str(getattr(product_type, "value", product_type)).strip().lower()

        matches = []
        if effective_query:
            # Step 1: Encode query to dense vector
            query_vector = self._encode_query(effective_query)

            # Step 2: Query Pinecone Vector Database with strict gender and product type filters
            response = self._query_pinecone_index(
                query_vector=query_vector,
                gender=gender,
                product_type=product_type,
                top_k=50,
            )
            matches = getattr(response, "matches", []) or []

        # Step 3: Fetch matching product records and compute blended ranking
        ranked_products = []
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
                product_type=product_type,
            )

            ranked_products = self._rank_pinecone_candidates(
                matches=matches,
                db_records=db_records,
                query=effective_query,
                gender=gender,
                product_type=product_type,
            )

        # Step 4: Keep only strictly in-stock items
        in_stock_results = [
            r for r in ranked_products
            if getattr(r.get("product"), "stock", 0) and r["product"].stock > 0
        ]

        if len(in_stock_results) >= limit:
            return in_stock_results[:limit]

        # Step 5: If top items were out of stock, backfill next items via local candidate search
        chosen_ids = [r["product_id"] for r in in_stock_results]
        needed = limit - len(in_stock_results)

        fallback_ranked = await self._run_fallback_local_search(
            user_id=user_id,
            gender=gender,
            query=effective_query,
            limit=needed,
            product_type=product_type,
            exclude_ids=chosen_ids,
        )

        for item in fallback_ranked:
            p = item.get("product")
            if p and getattr(p, "stock", 0) and p.stock > 0 and item["product_id"] not in chosen_ids:
                in_stock_results.append(item)
                chosen_ids.append(item["product_id"])
                if len(in_stock_results) >= limit:
                    break

        if len(in_stock_results) >= limit:
            return in_stock_results[:limit]

        # Step 6: If still fewer than limit, backfill with next in-stock products of this type
        needed = limit - len(in_stock_results)
        if product_type:
            type_fallback = await self.db.get_most_good_products_by_type(
                product_type=product_type,
                gender=gender,
                limit=needed,
                exclude_ids=chosen_ids,
            )
            for item in type_fallback:
                p = item.get("product")
                if p and getattr(p, "stock", 0) and p.stock > 0 and item["product_id"] not in chosen_ids:
                    in_stock_results.append({
                        "product_id": item["product_id"],
                        "product": p,
                        "cosine_similarity": 0.0,
                        "probability_score": item.get("score", 0.0),
                        "rank_score": round(item.get("score", 0.0) * 0.3, 4),
                        "source": "type_instock_backfill",
                    })
                    chosen_ids.append(item["product_id"])
                    if len(in_stock_results) >= limit:
                        break

        # Step 7: Cross-type global backfill ONLY if product_type was not specified
        if len(in_stock_results) < limit and not product_type:
            needed = limit - len(in_stock_results)
            global_fallback = await self.db.get_most_good_products_global(
                gender=gender,
                limit=needed,
                exclude_ids=chosen_ids,
            )

            for item in global_fallback:
                p = item.get("product")
                if p and getattr(p, "stock", 0) and p.stock > 0 and item["product_id"] not in chosen_ids:
                    in_stock_results.append({
                        "product_id": item["product_id"],
                        "product": p,
                        "cosine_similarity": 0.0,
                        "probability_score": item.get("score", 0.0),
                        "rank_score": round(item.get("score", 0.0) * 0.3, 4),
                        "source": "global_instock_backfill",
                    })
                    chosen_ids.append(item["product_id"])
                    if len(in_stock_results) >= limit:
                        break

        return in_stock_results[:limit]

    # 3. Overall top in-stock products (ProbabilityOfShowingItems + fallback)
    async def recommedMostGoodProduct(
        self,
        gender: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Finds top in-stock products globally from ProbabilityOfShowingItems."""
        return await self.db.get_most_good_products_global(
            gender=gender,
            limit=limit,
        )

    # 4. Top in-stock products by product type (ProbabilityOfShowingItems + fallback)
    async def recommedMostGoodProductByType(
        self,
        product_type: str,
        gender: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Finds top in-stock products of a given type from ProbabilityOfShowingItems."""
        return await self.db.get_most_good_products_by_type(
            product_type=product_type,
            gender=gender,
            limit=limit,
        )

    # 5. Products by type, query, gender & user_id (with in-stock guarantee and backfill)
    async def recommedTheUserProductByTypeAndQuery(
        self,
        user_id: int,
        product_type: str,
        gender: Optional[str] = None,
        user_query: str = "",
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Recommends products of a specific product type and gender for a given user,
        ranked by semantic query similarity blended with personalized user probability.
        
        Args:
            user_id: Target user ID for personalized scoring.
            product_type: Product category (e.g. 'jeans', 't-shirt', 'shirt', 'hoodie', 'short').
            gender: Optional gender filter ('men', 'women', 'unisex').
            user_query: Search or preference query text.
            limit: Maximum in-stock recommendations to return (default: 5).
        """
        return await self.recommedTheUserProductThroughQuery(
            user_id=user_id,
            gender=gender,
            user_query=user_query,
            product_type=product_type,
            limit=limit,
        )

    # Naming aliases for backwards compatibility and developer convenience
    recommedTheUserProduct = recommedTheUserPorduct
    getMostGoodProduct = recommedMostGoodProduct
    getMostGoodProductByType = recommedMostGoodProductByType
    recommedTheUserProductThroughQueryAndType = recommedTheUserProductByTypeAndQuery
    recommedTheUserProductByType = recommedTheUserProductByTypeAndQuery
    searchProductsByType = recommedTheUserProductByTypeAndQuery
    searchTheUserProductByType = recommedTheUserProductByTypeAndQuery


# Exported instances
recommedationController = Recommedation(
    db=recommendation_db,
    vector_db=vectorDB,
)
recommendationController = recommedationController
