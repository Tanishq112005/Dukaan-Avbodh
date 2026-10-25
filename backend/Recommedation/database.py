from typing import Optional, List, Dict, Any, Union
from sqlmodel import select, or_, func
from sqlalchemy import cast, String

from config.database import db_connection
from Product.models import Product, ProductType
from .models import (
    ProbabilityOfShowingItems,
    ProbabilityOfShowingItemsForParticularUser,
)


def resolve_product_type(val: Any) -> Optional[ProductType]:
    """Resolves a string or Enum value to a valid ProductType Enum member."""
    if not val:
        return None
    if isinstance(val, ProductType):
        return val

    clean = str(val).strip().lower().replace("-", "_").replace(" ", "_")
    raw_str = str(val).strip().lower()

    for member in ProductType:
        if member.name.lower() == clean or member.value.lower() == raw_str:
            return member

    return None


class RecommendationDatabase:
    """
    Database query layer for recommendations.
    Strictly guarantees that only in-stock products (stock > 0) are returned,
    and automatically backfills next in-stock products if top-scored items are out of stock.
    """

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

    def _apply_type(self, stmt, product_type: Optional[Union[str, ProductType]]):
        """
        Strict product type filter matching either via resolved ProductType Enum
        or case-insensitive casted string comparison.
        """
        if not product_type:
            return stmt

        resolved = resolve_product_type(product_type)
        if resolved is not None:
            return stmt.where(Product.type == resolved)

        clean_type = str(getattr(product_type, "value", product_type)).strip().lower()
        return stmt.where(cast(Product.type, String).ilike(clean_type))

    # 1. Top products for user by score & gender (with stock > 0 and automatic next-item backfill)
    async def get_user_best_products(
        self,
        user_id: int,
        gender: Optional[str] = None,
        product_type: Optional[str] = None,
        limit: int = 5,
        exclude_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        excluded = list(exclude_ids or [])

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

            if excluded:
                stmt = stmt.where(Product.id.not_in(excluded))

            stmt = self._apply_gender(stmt, gender)
            stmt = self._apply_type(stmt, product_type)
            stmt = stmt.order_by(
                ProbabilityOfShowingItemsForParticularUser.score.desc()
            ).limit(limit)

            rows = (await session.exec(stmt)).all()
            for p, s in rows:
                if p.stock and p.stock > 0:
                    results.append({"product_id": p.id, "score": s, "product": p})
                    excluded.append(p.id)

        # If user has fewer in-stock items than limit, backfill with next in-stock products
        if len(results) < limit:
            needed = limit - len(results)
            if product_type:
                type_fill = await self.get_most_good_products_by_type(
                    product_type=product_type,
                    gender=gender,
                    limit=needed,
                    exclude_ids=excluded,
                )
                results.extend(type_fill)
            else:
                global_fill = await self.get_most_good_products_global(
                    gender=gender,
                    limit=needed,
                    exclude_ids=excluded,
                )
                results.extend(global_fill)

        return results[:limit]

    # 2. Fetch specific products by IDs (returned from Vector DB) with stock > 0, gender & type filter
    async def get_products_by_ids_with_user_scores(
        self,
        product_ids: List[int],
        user_id: int,
        gender: Optional[str] = None,
        product_type: Optional[str] = None,
    ) -> Dict[int, Dict[str, Any]]:
        if not product_ids:
            return {}

        async with self.db.get_session() as session:
            # Strictly select only products with stock > 0
            stmt = (
                select(Product)
                .where(Product.id.in_(product_ids))
                .where(Product.stock > 0)
            )
            stmt = self._apply_gender(stmt, gender)
            stmt = self._apply_type(stmt, product_type)
            products = (await session.exec(stmt)).all()

            if not products:
                return {}

            matched_ids = [p.id for p in products if p.stock and p.stock > 0]
            if not matched_ids:
                return {}

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
                ProbabilityOfShowingItems.product_id,
                ProbabilityOfShowingItems.score,
            ).where(ProbabilityOfShowingItems.product_id.in_(matched_ids))
            global_scores = dict((await session.exec(global_stmt)).all())

            result = {}
            for p in products:
                if p.stock and p.stock > 0:
                    score = float(user_scores.get(p.id, global_scores.get(p.id, 0.0)))
                    result[p.id] = {"product": p, "score": score}

            return result

    # 3. Get in-stock candidate products for local fallback search
    async def get_candidates_for_query(
        self,
        user_id: int,
        gender: Optional[str] = None,
        product_type: Optional[str] = None,
        limit: int = 50,
        exclude_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        async with self.db.get_session() as session:
            stmt = select(Product).where(Product.stock > 0)

            if exclude_ids:
                stmt = stmt.where(Product.id.not_in(exclude_ids))

            stmt = self._apply_gender(stmt, gender)
            stmt = self._apply_type(stmt, product_type).limit(limit)
            products = (await session.exec(stmt)).all()

            if not products:
                return []

            matched_ids = [p.id for p in products if p.stock and p.stock > 0]
            if not matched_ids:
                return []

            user_stmt = select(
                ProbabilityOfShowingItemsForParticularUser.product_id,
                ProbabilityOfShowingItemsForParticularUser.score,
            ).where(
                ProbabilityOfShowingItemsForParticularUser.user_id == user_id,
                ProbabilityOfShowingItemsForParticularUser.product_id.in_(matched_ids),
            )
            user_scores = dict((await session.exec(user_stmt)).all())

            global_stmt = select(
                ProbabilityOfShowingItems.product_id,
                ProbabilityOfShowingItems.score,
            ).where(ProbabilityOfShowingItems.product_id.in_(matched_ids))
            global_scores = dict((await session.exec(global_stmt)).all())

            return [
                {
                    "product": p,
                    "score": float(user_scores.get(p.id, global_scores.get(p.id, 0.0))),
                }
                for p in products
                if p.stock and p.stock > 0
            ]

    # 4. Overall top products from ProbabilityOfShowingItems with automatic next-item backfill
    async def get_most_good_products_global(
        self,
        gender: Optional[str] = None,
        limit: int = 5,
        exclude_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        excluded = list(exclude_ids or [])

        async with self.db.get_session() as session:
            stmt = (
                select(Product, ProbabilityOfShowingItems.score)
                .join(
                    ProbabilityOfShowingItems,
                    Product.id == ProbabilityOfShowingItems.product_id,
                )
                .where(Product.stock > 0)
            )

            if excluded:
                stmt = stmt.where(Product.id.not_in(excluded))

            stmt = self._apply_gender(stmt, gender).order_by(
                ProbabilityOfShowingItems.score.desc()
            ).limit(limit)

            rows = (await session.exec(stmt)).all()
            for p, s in rows:
                if p.stock and p.stock > 0:
                    results.append({"product_id": p.id, "score": s, "product": p})
                    excluded.append(p.id)

            # If still fewer than limit (e.g. probability table lacked enough in-stock rows),
            # backfill from the Product table directly to guarantee next in-stock products
            if len(results) < limit:
                needed = limit - len(results)
                fallback_stmt = select(Product).where(Product.stock > 0)

                if excluded:
                    fallback_stmt = fallback_stmt.where(Product.id.not_in(excluded))

                fallback_stmt = self._apply_gender(fallback_stmt, gender).limit(needed)
                fallback_prods = (await session.exec(fallback_stmt)).all()

                for p in fallback_prods:
                    if p.stock and p.stock > 0:
                        results.append({"product_id": p.id, "score": 0.0, "product": p})
                        excluded.append(p.id)

        return results[:limit]

    # 5. Top products by product type with automatic next-item backfill
    async def get_most_good_products_by_type(
        self,
        product_type: str,
        gender: Optional[str] = None,
        limit: int = 5,
        exclude_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        excluded = list(exclude_ids or [])
        clean_type = product_type.strip().lower()

        async with self.db.get_session() as session:
            stmt = (
                select(Product, ProbabilityOfShowingItems.score)
                .join(
                    ProbabilityOfShowingItems,
                    Product.id == ProbabilityOfShowingItems.product_id,
                )
                .where(Product.stock > 0)
            )
            stmt = self._apply_type(stmt, product_type)

            if excluded:
                stmt = stmt.where(Product.id.not_in(excluded))

            stmt = self._apply_gender(stmt, gender).order_by(
                ProbabilityOfShowingItems.score.desc()
            ).limit(limit)

            rows = (await session.exec(stmt)).all()
            for p, s in rows:
                if p.stock and p.stock > 0:
                    results.append({"product_id": p.id, "score": s, "product": p})
                    excluded.append(p.id)

            # Backfill with remaining in-stock products of this type from Product table
            if len(results) < limit:
                needed = limit - len(results)
                fallback_stmt = select(Product).where(Product.stock > 0)
                fallback_stmt = self._apply_type(fallback_stmt, product_type)

                if excluded:
                    fallback_stmt = fallback_stmt.where(Product.id.not_in(excluded))

                fallback_stmt = self._apply_gender(fallback_stmt, gender).limit(needed)
                fallback_prods = (await session.exec(fallback_stmt)).all()

                for p in fallback_prods:
                    if p.stock and p.stock > 0:
                        results.append({"product_id": p.id, "score": 0.0, "product": p})
                        excluded.append(p.id)

        return results[:limit]


recommendation_db = RecommendationDatabase(db_connection)
