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
        if not gender:
            return stmt
        g = gender.strip().lower()
        return stmt.where(
            or_(
                func.lower(Product.gender) == g,
                func.lower(Product.gender) == "unisex",
                Product.gender == None,
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

        # Cold-start fallback: top global products
        return await self.get_most_good_products_global(gender=gender, limit=limit)

    # 2. Get candidate products for query search
    async def get_candidates_for_query(
        self, user_id: int, gender: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        async with self.db.get_session() as session:
            stmt = select(Product).where(Product.stock > 0)
            stmt = self._apply_gender(stmt, gender).limit(limit)
            products = (await session.exec(stmt)).all()
            if not products:
                return []

            # Map user scores
            user_stmt = select(
                ProbabilityOfShowingItemsForParticularUser.product_id,
                ProbabilityOfShowingItemsForParticularUser.score,
            ).where(ProbabilityOfShowingItemsForParticularUser.user_id == user_id)
            user_scores = dict((await session.exec(user_stmt)).all())

            # Map global scores
            global_stmt = select(
                ProbabilityOfShowingItems.product_id, ProbabilityOfShowingItems.score
            )
            global_scores = dict((await session.exec(global_stmt)).all())

            return [
                {
                    "product": p,
                    "score": float(user_scores.get(p.id, global_scores.get(p.id, 0.0))),
                }
                for p in products
            ]

    # 3. Overall top 4-5 products from ProbabilityOfShowingItems
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

    # 4. Top 4-5 products by product type from ProbabilityOfShowingItems
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

            # Fallback
            fallback_stmt = (
                select(Product)
                .where(func.lower(Product.type) == product_type.strip().lower())
                .where(Product.stock > 0)
            )
            fallback_stmt = self._apply_gender(fallback_stmt, gender).limit(limit)
            fallback_prods = (await session.exec(fallback_stmt)).all()
            return [{"product_id": p.id, "score": 0.0, "product": p} for p in fallback_prods]


recommendation_db = RecommendationDatabase(db_connection)
