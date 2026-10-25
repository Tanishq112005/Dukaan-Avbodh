from typing import Optional, List, Dict, Any
from sqlmodel import select, or_, func

from config.database import db_connection
from models.product import Product
from models.probabilityValues import (
    ProbabilityOfShowingItems,
    ProbabilityOfShowingItemsForParticularUser,
)


class RecommendationDatabase:
    """Database query layer for recommendations, passed via __init__."""

    def __init__(self, db=None):
        self.db = db or db_connection

    def _apply_gender(self, stmt, gender: Optional[str]):
        """
        Strict gender filter: matches the requested gender or unisex products.
        Excludes opposite-gender items entirely.
        """
        if not gender:
            return stmt

        g = gender.strip().lower()
        return stmt.where(
            or_(
                func.lower(Product.gender) == g,
                func.lower(Product.gender) == "unisex",
            )
        )

    # 1. Top 4-5 products for user from ProbabilityOfShowingItemsForParticularUser
    async def get_user_best_products(
        self, user_id: int, gender: Optional[str] = None, limit: int = 5
    ) -> List[Dict[str, Any]]:
        async with self.db.get_session() as session:
            stmt = (
                select(Product, ProbabilityOfShowingItemsForParticularUser.score)
                .join(
                    ProbabilityOfShowingItemsForParticularUser,
                    Product.id == ProbabilityOfShowingItemsForParticularUser.product_id,
                )
                .where(ProbabilityOfShowingItemsForParticularUser.user_id == user_id)
                .where(Product.stock > 0)
            )
            stmt = self._apply_gender(stmt, gender).order_by(
                ProbabilityOfShowingItemsForParticularUser.score.desc()
            ).limit(limit)

            rows = (await session.exec(stmt)).all()
            if rows:
                return [{"product_id": p.id, "score": s, "product": p} for p, s in rows]

        # Cold-start fallback: top global products matching gender
        return await self.get_most_good_products_global(gender=gender, limit=limit)

    # 2. Fetch specific products by IDs (returned from Vector DB) with strict gender enforcement
    async def get_products_by_ids_with_user_scores(
        self, product_ids: List[int], user_id: int, gender: Optional[str] = None
    ) -> Dict[int, Dict[str, Any]]:
        if not product_ids:
            return {}

        async with self.db.get_session() as session:
            stmt = (
                select(Product)
                .where(Product.id.in_(product_ids))
                .where(Product.stock > 0)
            )
            # Strictly enforce gender matching in the SQL query
            stmt = self._apply_gender(stmt, gender)
            products = (await session.exec(stmt)).all()
            if not products:
                return {}

            matched_ids = [p.id for p in products]

            # Personalized scores for user
            user_stmt = select(
                ProbabilityOfShowingItemsForParticularUser.product_id,
                ProbabilityOfShowingItemsForParticularUser.score,
            ).where(
                ProbabilityOfShowingItemsForParticularUser.user_id == user_id,
                ProbabilityOfShowingItemsForParticularUser.product_id.in_(matched_ids),
            )
            user_scores = dict((await session.exec(user_stmt)).all())

            # Global scores fallback
            global_stmt = select(
                ProbabilityOfShowingItems.product_id, ProbabilityOfShowingItems.score
            ).where(ProbabilityOfShowingItems.product_id.in_(matched_ids))
            global_scores = dict((await session.exec(global_stmt)).all())

            result = {}
            for p in products:
                score = float(user_scores.get(p.id, global_scores.get(p.id, 0.0)))
                result[p.id] = {"product": p, "score": score}

            return result

    # 3. Get candidate products for local fallback search (with strict gender filter)
    async def get_candidates_for_query(
        self, user_id: int, gender: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        async with self.db.get_session() as session:
            stmt = select(Product).where(Product.stock > 0)
            stmt = self._apply_gender(stmt, gender).limit(limit)
            products = (await session.exec(stmt)).all()
            if not products:
                return []

            matched_ids = [p.id for p in products]

            user_stmt = select(
                ProbabilityOfShowingItemsForParticularUser.product_id,
                ProbabilityOfShowingItemsForParticularUser.score,
            ).where(
                ProbabilityOfShowingItemsForParticularUser.user_id == user_id,
                ProbabilityOfShowingItemsForParticularUser.product_id.in_(matched_ids)
            )
            user_scores = dict((await session.exec(user_stmt)).all())

            global_stmt = select(
                ProbabilityOfShowingItems.product_id, ProbabilityOfShowingItems.score
            ).where(ProbabilityOfShowingItems.product_id.in_(matched_ids))
            global_scores = dict((await session.exec(global_stmt)).all())

            return [
                {
                    "product": p,
                    "score": float(user_scores.get(p.id, global_scores.get(p.id, 0.0))),
                }
                for p in products
            ]

    # 4. Overall top 4-5 products from ProbabilityOfShowingItems
    async def get_most_good_products_global(
        self, gender: Optional[str] = None, limit: int = 5
    ) -> List[Dict[str, Any]]:
        async with self.db.get_session() as session:
            stmt = (
                select(Product, ProbabilityOfShowingItems.score)
                .join(
                    ProbabilityOfShowingItems,
                    Product.id == ProbabilityOfShowingItems.product_id,
                )
                .where(Product.stock > 0)
            )
            stmt = self._apply_gender(stmt, gender).order_by(
                ProbabilityOfShowingItems.score.desc()
            ).limit(limit)

            rows = (await session.exec(stmt)).all()
            if rows:
                return [{"product_id": p.id, "score": s, "product": p} for p, s in rows]

            # Stock fallback if probability table has not been computed yet
            fallback_stmt = select(Product).where(Product.stock > 0)
            fallback_stmt = self._apply_gender(fallback_stmt, gender).limit(limit)
            fallback_prods = (await session.exec(fallback_stmt)).all()
            return [{"product_id": p.id, "score": 0.0, "product": p} for p in fallback_prods]

    # 5. Top 4-5 products by product type from ProbabilityOfShowingItems
    async def get_most_good_products_by_type(
        self, product_type: str, gender: Optional[str] = None, limit: int = 5
    ) -> List[Dict[str, Any]]:
        async with self.db.get_session() as session:
            stmt = (
                select(Product, ProbabilityOfShowingItems.score)
                .join(
                    ProbabilityOfShowingItems,
                    Product.id == ProbabilityOfShowingItems.product_id,
                )
                .where(func.lower(Product.type) == product_type.strip().lower())
                .where(Product.stock > 0)
            )
            stmt = self._apply_gender(stmt, gender).order_by(
                ProbabilityOfShowingItems.score.desc()
            ).limit(limit)

            rows = (await session.exec(stmt)).all()
            if rows:
                return [{"product_id": p.id, "score": s, "product": p} for p, s in rows]

            fallback_stmt = (
                select(Product)
                .where(func.lower(Product.type) == product_type.strip().lower())
                .where(Product.stock > 0)
            )
            fallback_stmt = self._apply_gender(fallback_stmt, gender).limit(limit)
            fallback_prods = (await session.exec(fallback_stmt)).all()
            return [{"product_id": p.id, "score": 0.0, "product": p} for p in fallback_prods]


recommendation_db = RecommendationDatabase(db_connection)
